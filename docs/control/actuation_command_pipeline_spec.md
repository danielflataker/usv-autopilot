# Actuation command pipeline spec (V1.1 draft)

This document defines the end-to-end actuation command pipeline with one canonical set of names and symbols.
The goal is a stable structure that stays clean when small features are added later.

## Scope
- Applies to both `AUTOPILOT` and `MANUAL` command paths
- Defines stage-by-stage inputs/outputs
- Defines where command scaling is applied
- Defines canonical symbols, field names, and parameter names

## Design goals
1. One canonical naming scheme across control, mixer, logging, telemetry, and simulation.
2. One shared backend pipeline for `AUTOPILOT` and `MANUAL` after source-specific shaping.
3. Separation of concerns:
   - command shaping (operator/controller feel)
   - feasibility and priority (allocator)
   - motor safety/physical enforcement (motor shaping + ESC mapping)
4. Anti-windup based on achieved actuation (`u_*^{ach}`), not guessed limits.

## Canonical symbols and names

### Core actuation variables
| Stage | Math symbol | Field names | Description |
|---|---|---|---|
| Source request | $u_s^{req}, u_d^{req}$ | `u_s_req`, `u_d_req` (`ACTUATOR_REQ`) | Raw request from controller or RC mapping |
| Command-stage output | $u_s^{cmd}, u_d^{cmd}$ | `u_s_cmd`, `u_d_cmd` (`ACTUATOR_CMD`) | Shaped request forwarded to allocator |
| Allocator output | $u_s^{alloc}, u_d^{alloc}$ | `u_s_alloc`, `u_d_alloc` (optional debug) | Feasible command before motor-stage shaping |
| Achieved output | $u_s^{ach}, u_d^{ach}$ | `u_s_ach`, `u_d_ach` (`MIXER_FEEDBACK`) | Final achieved command after motor constraints |
| Motor outputs | $u_L, u_R$ | `u_L`, `u_R` (`ESC_OUTPUT`) | Per-motor normalized command after limits |

### Limit parameters
| Category | Math symbol | Parameter names |
|---|---|---|
| Hardware motor bounds | $u_{LR,min}, u_{LR,max}$ | `act.hw.u_LR_min`, `act.hw.u_LR_max` |
| Software motor envelope | $u_{LR,min}^{sw}, u_{LR,max}^{sw}$ | `act.sw.u_LR_min`, `act.sw.u_LR_max` |
| Software surge envelope | $u_s^{min}, u_s^{max}$ | `act.sw.u_s_min`, `act.sw.u_s_max` |
| Software differential envelope | $u_{d,max}^{-}, u_{d,max}^{+}$ | `act.sw.u_d_max_neg`, `act.sw.u_d_max_pos` |

### Scaling parameters (new)
| Mode | Math symbol | Parameter names | Description |
|---|---|---|---|
| AUTOPILOT surge scale | $k_s^{ap}$ | `act.shp.ap.u_s_scale` | Optional global attenuation of surge request |
| AUTOPILOT differential scale | $k_d^{ap}$ | `act.shp.ap.u_d_scale` | Optional global attenuation of differential request |
| MANUAL surge scale | $k_s^{man}$ | `act.shp.man.u_s_scale` | RC feel/safety scaling in surge axis |
| MANUAL differential scale | $k_d^{man}$ | `act.shp.man.u_d_scale` | RC feel/safety scaling in yaw axis |

Scaling gains are dimensionless and default to `1.0`.

## Pipeline definition

## Stage 0 — source generation
Purpose: produce raw actuation request.

Inputs:
- `AUTOPILOT`: controller outputs (`u_s_raw`, `u_d_raw`) from speed/yaw loops
- `MANUAL`: RC channels mapped to normalized request axes

Outputs:
- $u_s^{req}, u_d^{req}$

Rules:
- Stage 0 contains no feasibility logic.
- Stage 0 does not write motor outputs.

## Stage 1 — command shaping (mode-specific)
Purpose: shape request before allocator.

Detailed stage definition is documented in [`command_shaping.md`](command_shaping.md).

Inputs:
- $u_s^{req}, u_d^{req}$
- mode-specific shaping parameters
- command envelopes

Output:
- $u_s^{cmd}, u_d^{cmd}$ (`ACTUATOR_CMD`)

Command shaping owns source feel/sensitivity and pre-allocation command envelopes.

## Stage 2 — allocator (policy + feasibility)
Purpose: enforce feasibility and priority policy in $(u_s,u_d)$ space.

Inputs:
- $u_s^{cmd}, u_d^{cmd}$
- software motor envelope and hardware motor bounds
- allocator policy (`ALLOC_SPEED_PRIORITY`, `ALLOC_YAW_PRIORITY`, later `ALLOC_WEIGHTED`)

Output:
- $u_s^{alloc}, u_d^{alloc}$

Policy contract:
- `ALLOC_SPEED_PRIORITY`: preserve $u_s$ first, reduce $u_d$ as needed
- `ALLOC_YAW_PRIORITY`: preserve $u_d$ first, reduce $u_s$ as needed
- `ALLOC_WEIGHTED`: minimize weighted command error under constraints

## Stage 3 — mixer + motor-stage shaping
Purpose: convert allocator output to per-motor command and enforce motor-side constraints.

Inputs:
- $u_s^{alloc}, u_d^{alloc}$
- motor envelopes/bounds, trims, slew parameters

Operations (ordered):
1. Mix:
   - $u_L = u_s^{alloc} - u_d^{alloc}$
   - $u_R = u_s^{alloc} + u_d^{alloc}$
2. Apply trims/calibration
3. Clamp to motor envelope and hardware bounds
4. Apply idle/deadband and slew-rate limits

Outputs:
- `ESC_OUTPUT`: $u_L, u_R$
- achieved stage reconstructed from outputs:
  - $u_s^{ach} = 0.5(u_L + u_R)$
  - $u_d^{ach} = 0.5(u_R - u_L)$

## Stage 4 — feedback for control/logging
Purpose: publish achieved values and saturation state.

Outputs:
- `MIXER_FEEDBACK`: `u_s_ach`, `u_d_ach`, `sat_L`, `sat_R`, `sat_any`
- optional diagnostics:
  - `sat_cmd_stage`, `sat_alloc`, `sat_motor_stage`
  - `u_s_max_eff`, `u_d_max_pos_eff`, `u_d_max_neg_eff`, `u_LR_max_eff`, `u_LR_min_eff`

Control rule:
- Anti-windup uses achieved-vs-commanded deltas:
  - $u_s^{ach} - u_s^{cmd}$
  - $u_d^{ach} - u_d^{cmd}$

## Scaling policy by mode

### AUTOPILOT
- Default: $k_s^{ap}=1.0$, $k_d^{ap}=1.0$.
- Primary safety/behavior control remains limits + allocator policy.
- Scaling is available as an explicit tuning knob, not as a substitute for feasibility handling.

### MANUAL
- Default: reduced yaw sensitivity is allowed through $k_d^{man} < 1.0$.
- Full-stick behavior is tuned in command shaping, not by bypassing allocator.
- Backend stages (allocator, mixer, motor shaping, feedback) remain shared with autopilot.

## Invariants and validation rules
1. `act.hw.u_LR_min <= act.sw.u_LR_min <= act.sw.u_LR_max <= act.hw.u_LR_max`
2. `act.sw.u_d_max_neg >= 0`, `act.sw.u_d_max_pos >= 0`
3. `act.shp.*.u_s_scale >= 0`, `act.shp.*.u_d_scale >= 0`
4. `ACTUATOR_CMD` always carries `u_s_cmd`, `u_d_cmd` after command shaping
5. Anti-windup always uses `MIXER_FEEDBACK` achieved values

## Integration plan (documentation-first)
1. Add this spec and make it the naming reference for actuation pipeline changes.
2. Update `control/overview.md` and `control/mixer_and_limits.md` to link this spec as canonical stage definition.
3. Keep `interfaces/contracts.md` and `interfaces/dataflow.md` aligned with `ACTUATOR_REQ` + `ACTUATOR_CMD` stage contracts.
4. Add logging field plan for optional `u_*_req` and `u_*_alloc` visibility.
5. Implement in code in small steps: Stage 1 shaping first, then allocator policy parameterization, then diagnostics.

## Docs consistency check

A lightweight naming check is available to catch drift across core documents:

```bash
python tools/check_docs_contracts.py
```

The script validates required topics (`ACTUATOR_REQ`, `ACTUATOR_CMD`, `MIXER_FEEDBACK`) and stage naming (`req/cmd/alloc/ach`) across:
- `docs/interfaces/contracts.md`
- `docs/interfaces/dataflow.md`
- `docs/control/mixer_and_limits.md`
