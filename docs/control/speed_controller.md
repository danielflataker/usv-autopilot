# Speed controller (V1)

Purpose: track desired surge speed $v_d$ by producing the average request component $u_s^{req}$.
Yaw control produces $u_d^{req}$ separately; together they form the request-stage vector $\mathbf{q}=[u_s^{req},u_d^{req}]^\top$ before command shaping maps to $(u_s^{cmd},u_d^{cmd})$.

## Inputs
- desired speed $v_d$ (from `docs/guidance/`)
- estimated surge speed $\hat v$ (from `NAV_SOLUTION`)
- sample time $\Delta t$

## Output
- average request $u_s^{req}$ (normalized request stage)
- optional debug: $e_v$, integrator state, saturation flags

## Error signal
$e_v = v_d - \hat v$

## Controller form (start simple)
V1 baseline is PI:
- proportional: $u_P = k_p e_v$
- integral: $u_I[k] = u_I[k-1] + k_i\,e_v\,\Delta t$
- raw command: $u_s^{*} = u_P + u_I$

Maybe later: feedforward $u_{ff}$ once the thrust-to-speed mapping is identified:
- $u_s^{*} = u_{ff}(v_d) + u_P + u_I$

## Saturation and anti-windup
Request stage passes raw controller output; command-stage limits are applied in command shaping:
- baseline `AUTOPILOT` contract: $u_s^{req} = u_s^{*}$ (source-specific request-space bounds may also be applied before shaping)

Anti-windup (choose one implementation):
- freeze integrator when saturated and $e_v$ pushes further into saturation
- back-calculation (more work, smoother)

(Exact clamp/slew is handled in `../actuation/mixer_and_limits.md`, but the controller still needs an anti-windup rule.)

## Special cases / validity
- If $\hat v$ is flagged invalid (estimator unhealthy), optionally fall back to GNSS ground speed when available and above a minimum speed.
- At very low speed, noise can dominate; consider a small deadband on $e_v$ (TBD).

## Logging (recommended)
Log at control rate:
- $v_d$, $\hat v$, $e_v$
- $u_s^{*}$, $u_s^{req}$, saturation flag
- integrator value (for tuning / debugging)

## Saturation + anti-windup (V1)

Actuation may clip at command stage and again at motor stage; final achieved actuation is set by motor-stage limits/slew.
Controllers should use achieved-vs-command residuals in hardware-normalized space for anti-windup.

Contract:
- `MIXER_FEEDBACK -> mixer_feedback_t` is defined in [docs/interfaces/contracts.md](../interfaces/contracts.md).

Rule of thumb:
- Each controller compares what it *commanded* vs what was *achieved*:
  - speed loop uses $(u_s^{ach} - u_s^{cmd})$
  - yaw-rate loop uses $(u_d^{ach} - u_d^{cmd})$

Typical implementation options (pick one later):
- Freeze/clamp integration when `sat_any` is true and the error would push further into saturation.
- Back-calculation (tracking) using the achieved-vs-commanded difference.

Notes:
- Priority (hold yaw vs hold speed) is owned by the mixer/allocator policy, not by the PI loops.
- Keep the controller math independent of whether the ESC supports reverse; that mapping is handled downstream.

## TODO / Open questions
- PI vs PID
- add $u_{ff}(v_d)$ after identifying $(k_v,\tau_v)$ from water tests
- define limits for $u_s^{req}$ and command-stage shaping behavior on mode switch
