# Control overview (V1)

This folder describes the V1 control stack: track heading and speed, then mix to left/right motor commands for a twin-prop boat (no rudder).

Inputs:
- references from [`docs/guidance/`](../guidance/overview.md)
- state estimates from [`docs/estimation/`](../estimation/overview.md)

## What control produces (internal)
The controller outputs the canonical internal actuator commands (command stage):
- average command $u_s^{cmd}$ (surge)
- differential command $u_d^{cmd}$ (yaw)

In payloads these are carried as `u_s_cmd`, `u_d_cmd` inside `actuator_cmd_t` (see `interfaces/contracts.md`).
They are mixed into per-motor commands $(u_L,u_R)$ in [`mixer_and_limits.md`](mixer_and_limits.md) and then mapped to PWM by the ESC driver.

## Files
- [`cascaded_heading_yawrate.md`](cascaded_heading_yawrate.md) — yaw control: $e_\psi \rightarrow r_d \rightarrow u_d^{cmd}$
- [`speed_controller.md`](speed_controller.md) — speed control: $e_v \rightarrow u_s^{cmd}$
- [`mixer_and_limits.md`](mixer_and_limits.md) — $(u_s^{cmd},u_d^{cmd}) \rightarrow (u_L,u_R)$ + clamp/idle/slew

## V1 control pipeline (short)
1) Guidance provides $\psi_d$ and $v_d$
2) Yaw control computes $u_d^{cmd}$
3) Speed control computes $u_s^{cmd}$
4) Mixer + limits produce $(u_L,u_R)$ and feedback $(u_s^{ach},u_d^{ach})$

Detailed stage definitions and naming invariants are specified in [`actuation_command_pipeline_spec.md`](actuation_command_pipeline_spec.md).

## Notes
- Saturation happens after mixing, so controllers should use mixer feedback (`MIXER_FEEDBACK`) for anti-windup (see `interfaces/contracts.md`).

## Open questions
- Controller forms: P vs PI for heading loop, PI for speed/yaw-rate loops
- Anti-windup choice: freeze vs back-calculation (using mixer feedback)
- Limits: $r_{\max}$, $u_{d,\max}$, motor range, slew rates
- Safe behavior at low speed / poor heading observability
- Add tuning procedures and expected plots (link to `docs/ops/`)