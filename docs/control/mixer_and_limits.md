# Mixer, allocator, and limits (V1)

This page defines the *actuator pipeline* from controller commands $(u_s^{cmd},u_d^{cmd})$ to per-motor outputs $(u_L,u_R)$, and where saturation/feedback is generated.

Goal: make it easy to swap allocation policy (speed-priority vs yaw-priority vs later cost/QP) without rewriting the rest.

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
- `MIXER_FEEDBACK → mixer_feedback_t` (recommended): achieved $(u_s^{ach},u_d^{ach})$ + saturation flags for anti-windup

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
- **Later:** weighted least-squares / QP (minimize error in $u_s^{cmd}$ and $u_d^{cmd}$ under constraints)

Notes:
- The allocator should be a small, swappable function with a stable signature.
- It should not know about PWM, only normalized commands + limits.

Open questions:
- Default policy for AUTOPILOT vs MANUAL?
- How to handle “no reverse” (clamp negative motor commands) in the feasible set?

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

Controllers then do anti-windup using either:

* **Freeze/clamp integration** when saturated in the “wrong” direction, or
* **Back-calculation (tracking):** use $(u_*^{ach}-u_*^{cmd})$.

Notation reminder (for consistency across docs):
- $u_*^{cmd}$: from controller to allocator (`ACTUATOR_CMD`)
- $u_*^{ach}$: returned by mixer/limits (`MIXER_FEEDBACK`)

## About thrust/force models and unit conversions

We keep this module in **normalized command space**. Anything like “$u \rightarrow$ Newton” or “$u \rightarrow$ steady-state speed” is a *propulsion model* and should live elsewhere.

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
