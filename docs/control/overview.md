# Control overview (V1)

This folder describes the V1 control stack: track heading and speed, then mix to left/right motor commands for a twin-prop boat (no rudder).

Inputs:
- references from [`docs/guidance/`](../guidance/overview.md)
- state estimates from [`docs/estimation/`](../estimation/overview.md)

## What control produces (internal)
The controller outputs the canonical internal actuator commands:
- average command $u_s$ (surge)
- differential command $u_d$ (yaw)

These are mixed into per-motor commands $(u_L,u_R)$ in [`mixer_and_limits.md`](mixer_and_limits.md) and then mapped to PWM by the ESC driver.

## Files
- [`cascaded_heading_yawrate.md`](cascaded_heading_yawrate.md) — yaw control: $e_\psi \rightarrow r_d \rightarrow u_d$
- [`speed_controller.md`](speed_controller.md) — speed control: $e_v \rightarrow u_s$
- [`mixer_and_limits.md`](mixer_and_limits.md) — $(u_s,u_d) \rightarrow (u_L,u_R)$ + clamp/idle/slew

## V1 control pipeline (short)
1) Guidance provides $\psi_d$ and $v_d$
2) Yaw control computes $u_d$
3) Speed control computes $u_s$
4) Mixer + limits produce $(u_L,u_R)$ for the ESCs

## Notes
- Saturation happens after mixing, so controllers should use mixer feedback (`MIXER_FEEDBACK`) for anti-windup (see `interfaces/contracts.md`).

## Open questions
- Controller forms: P vs PI for heading loop, PI for speed/yaw-rate loops
- Anti-windup choice: freeze vs back-calculation (using mixer feedback)
- Limits: $r_{\max}$, $u_{d,\max}$, motor range, slew rates
- Safe behavior at low speed / poor heading observability
- Add tuning procedures and expected plots (link to `docs/ops/`)