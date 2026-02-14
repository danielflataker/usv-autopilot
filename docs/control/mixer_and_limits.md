# Mixer, allocator, and limits (V1)

This page defines the *actuator pipeline* from controller commands $(u_s^{cmd},u_d^{cmd})$ to per-motor outputs $(u_L,u_R)$, and where saturation/feedback is generated.

Goal: V1 keeps allocation policy swappable (speed-priority, yaw-priority, later cost/QP) without rewriting the rest of the module.

## What this module does (in order)
1) **Allocator**: choose achievable $(u_s^{ach},u_d^{ach})$ given limits + policy  
2) **Mixer**: map $(u_s^{ach},u_d^{ach}) \rightarrow (u_L,u_R)$  
3) **Shaping**: trims, clamp, idle/deadband, slew-rate  
4) **Feedback**: publish what was actually achieved for anti-windup

## Inputs / outputs
Inputs:
- $(u_s^{cmd},u_d^{cmd})$ from control via `ACTUATOR_CMD → actuator_cmd_t` (`u_s_cmd`, `u_d_cmd`)
- motor limits + policy params + $\Delta t$

Outputs:
- `ESC_OUTPUT → esc_output_t`: $(u_L,u_R)$ (internal motor commands; ESC driver maps to PWM)
- `MIXER_FEEDBACK → mixer_feedback_t`: achieved $(u_s^{ach},u_d^{ach})$ + saturation flags for anti-windup

(Exact payload fields are defined in [`interfaces/contracts.md`](../interfaces/contracts.md).)

---

## 1) Allocator (policy layer)

The allocator decides what part of the requested command is feasible under motor limits.
It owns the “what to preserve under saturation” policy.

Inputs: $(u_s^{cmd},u_d^{cmd})$  
Outputs: $(u_s^{ach},u_d^{ach})$ + saturation flags

Policies (V1 candidates):
- **Speed-priority:** preserve $u_s^{cmd}$ as much as possible, reduce $u_d^{cmd}$ when needed
- **Yaw-priority:** preserve $u_d^{cmd}$ as much as possible, adjust $u_s^{cmd}$ when needed
- **Weighted/cost-based (later):** weighted least-squares / QP (minimize error in $u_s^{cmd}$ and $u_d^{cmd}$ under constraints)

Notes:
- The allocator is implemented as a small, swappable function with a stable signature.
- The allocator operates on normalized commands + limits and does not include PWM details.

Open questions:
- Default policy for AUTOPILOT vs MANUAL?
- How to handle “no reverse” (clamp negative motor commands) in the feasible set?

### Hardware limits vs software envelopes

V1 uses two separate layers:

1. **Hardware limits (absolute):** what ESC + propulsion can physically do.
   - Internal normalization still means `u=1.0` is “max physically possible”.
   - These limits change rarely at runtime.
2. **Software envelopes (operational):** what we *allow* in normal operation.
   - Safety/tuning choices, e.g. cap surge authority to reduce aggressive behavior.
   - These are mode- and mission-dependent and can be parameters.

Practical V1 structure:

- Envelope A (command-stage): clamp controller outputs before allocation
  - `u_s_cmd ∈ [u_s_min, u_s_max]`
  - `u_d_cmd ∈ [-u_d_max_neg, u_d_max_pos]`
- Envelope B (motor-stage): clamp mixed outputs before ESC output
  - `u_L,u_R ∈ [u_LR_min, u_LR_max]`

Then allocator + mixer enforce feasibility under both software envelopes and hardware limits.

Recommended limit names (all tunable):
- motor absolute max/min: `u_LR_max`, `u_LR_min` (math: $u_{LR,max}, u_{LR,min}$)
- surge envelope: `u_s_max`, `u_s_min` (math: $u_s^{max}, u_s^{min}$)
- differential envelope: `u_d_max_pos`, `u_d_max_neg` (math: $u_{d,max}^{+}, u_{d,max}^{-}$)

When reverse is disabled, V1 uses separate positive/negative limits for `u_d` because feasible yaw authority is direction-dependent.

This directly enables the use-case “hold `u_s=0.7`, then add yaw authority” by reserving motor headroom through `u_s_max < u_LR_max`.
Trade-off: reduced max straight-line acceleration/top speed.

### Feasibility intuition (why headroom helps)

With

```math
u_L = u_s - u_d,\qquad u_R = u_s + u_d,
```

and motor limits `u_{LR,min} <= u_L,u_R <= u_{LR,max}`, the feasible `u_d` interval is:

```math
u_d \in [\max(u_s-u_{LR,max},\;u_{LR,min}-u_s),\;\min(u_s-u_{LR,min},\;u_{LR,max}-u_s)].
```

This is the general form and works both with and without reverse thrust.

Useful special case (symmetric range, e.g. `[-1,1]`):

```math
|u_d| \le u_{LR,max} - |u_s|.
```

No-reverse case (range `[0,1]`) is asymmetric:
- positive `u_d` is limited by `1-u_s`
- negative `u_d` is limited by `u_s`

So if `u_s` is high, there is little room left for positive `u_d`; if `u_s` is low, there is little room left for negative `u_d`.
A software surge cap (for example `u_s_max=0.7`) still preserves differential margin, but available margin depends on direction when reverse is not allowed.

## 2) Mixer (pure mapping)

Once $(u_s^{ach},u_d^{ach})$ are decided, mixing is just algebra:

```math
u_L = u_s^{ach} - u_d^{ach}, \qquad
u_R = u_s^{ach} + u_d^{ach}.
```

Inverse (useful for feedback/debug):

```math
u_s^{ach} = \tfrac12(u_L+u_R), \qquad
u_d^{ach} = \tfrac12(u_R-u_L).
```

Sign convention (explicit): positive differential command means right motor command is larger than left motor command ($u_R>u_L$).

## 3) Shaping (limits, idle, slew)

Shaping is applied to $(u_L,u_R)$ after mixing.

Order (V1):

1. Optional trims/calibration (static offsets/scales)
2. Clamp to allowed motor range ($u_{\min}, u_{\max}$ per motor)
3. Idle/deadband (optional; depends on ESC + reverse support)
4. Slew-rate limiting on $u_L/u_R$ (up/down may differ)
5. Write `ESC_OUTPUT` (non-blocking); ESC driver maps internal $(u_L,u_R)$ to PWM

### Command range (normalized)

The ESC/motor setup ultimately decides whether reverse is available.

V1 choice: keep one internal convention and map to ESC output:

* internal: $u_L,u_R \in [-1,1]$ (signed, $0$ is stop)
* ESC mapping: convert to PWM / clamp if reverse is not supported

This file defines the internal convention; the ESC driver implements the final mapping.

## 4) Saturation feedback (anti-windup)

True saturation is only known after motor clamping (and possibly slew).
To avoid integrator windup, publish `MIXER_FEEDBACK` based on what was actually achieved:

* achieved commands: $u_s^{ach},u_d^{ach}$
* flags: `sat_L`, `sat_R`, `sat_any`

Extra diagnostics (V1.1):

* `sat_cmd_stage` (command envelope active)
* `sat_alloc` (allocator had to change `u_s/u_d` for feasibility)
* `sat_motor_stage` (motor clamp/slew active)
* effective limits used this cycle (`u_s_max_eff`, `u_d_max_pos_eff`, `u_d_max_neg_eff`, `u_LR_max_eff`, `u_LR_min_eff`)

Controllers then do anti-windup using either:

* **Freeze/clamp integration** when saturated in the “wrong” direction, or
* **Back-calculation (tracking):** use $(u_*^{ach}-u_*^{cmd})$.

### Recommended signal stages

Keep the signal set small so it is easy to reason about saturation.

Required in V1 control logic:

1. **Requested command** (`u_*^{cmd}`)
   - what the controller/PID asked for
2. **Final achieved command** (`u_*^{ach}` from final motor outputs)
   - what was actually sent to the plant

These two are enough for anti-windup and for analyzing "requested vs achieved" behavior.

Optional intermediate stage:

- `u_*^{alloc}` (allocator result after command-stage limits, before final motor shaping)

Treat `u_*^{alloc}` as debug/tuning data, not as a required control input.

V1 tracks command (`u_*^{cmd}`) and final achieved output (`u_*^{ach}`) as mandatory signals; allocator-stage signals are optional diagnostics.

Notation reminder (for consistency across docs):
- $u_*^{cmd}$: from controller to allocator (`ACTUATOR_CMD`)
- $u_*^{alloc}$: optional allocator/intermediate result (debug/tuning)
- $u_*^{ach}$: final achieved command returned by mixer/limits (`MIXER_FEEDBACK`)

## About thrust/force models and unit conversions

This module uses **normalized command space**. Any mapping like “$u \rightarrow$ Newton” or “$u \rightarrow$ steady-state speed” belongs to a separate *propulsion model* document.

Proposed separation:

* **Allocator/mixer/shaping**: normalized $u$ only, cares about limits + safety
* **Propulsion model (later)**: maps $u$ to approximate thrust/force or to a velocity model

  * used for analysis, feedforward, simulation, or future model-based control
  * not required for V1 to work

If we later want Newtons:

* add a `propulsion_model.md` (or `hardware/propulsion.md`) describing:

  * $F_L \approx f(u_L)$, $F_R \approx f(u_R)$ (possibly nonlinear)
  * optional inverse mapping for feedforward
* keep the controller’s primary output as $(u_s^{cmd},u_d^{cmd})$ (carried as `u_s_cmd`,`u_d_cmd` in `actuator_cmd_t`) unless we *explicitly* redesign control to output force.

## Open questions

* Do we need a simple static map $u \rightarrow F$ early (for logging/plots), or can it wait?
* If we add a thrust model, do we apply it before or after shaping (usually after, because shaping changes what is actually commanded)?
