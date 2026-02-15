# Control overview (V1)

This folder describes the V1 control stack: track heading and speed, then mix to left/right motor commands for a twin-prop boat (no rudder).

Inputs:
- references from [`docs/guidance/`](../guidance/overview.md)
- state estimates from [`docs/estimation/`](../estimation/overview.md)

## What control produces (internal)
The controller produces request-stage actuation terms:
- average request $u_s^{req}$ (surge)
- differential request $u_d^{req}$ (yaw)

Command shaping then produces command-stage terms `u_s_cmd`, `u_d_cmd` for allocation and mixing.
The final mapping to $(u_L,u_R)$ is defined in [`mixer_and_limits.md`](mixer_and_limits.md).

## Files
- [`cascaded_heading_yawrate.md`](cascaded_heading_yawrate.md) — yaw control: $e_\psi \rightarrow r_d \rightarrow u_d^{req}$
- [`speed_controller.md`](speed_controller.md) — speed control: $e_v \rightarrow u_s^{req}$
- [`command_shaping.md`](command_shaping.md) — $(u_s^{req},u_d^{req}) \rightarrow (u_s^{cmd},u_d^{cmd})$ with scaling/deadband/envelope clamp
- [`mixer_and_limits.md`](mixer_and_limits.md) — $(u_s^{cmd},u_d^{cmd}) \rightarrow (u_L,u_R)$ + clamp/idle/slew

## V1 control pipeline (short)
1) Guidance provides $\psi_d$ and $v_d$
2) Yaw/speed control computes request stage $(u_s^{req},u_d^{req})$
3) Command shaping computes command stage $(u_s^{cmd},u_d^{cmd})$
4) Allocator + mixer + limits produce $(u_L,u_R)$ and feedback $(u_s^{ach},u_d^{ach})$

Detailed stage definitions and naming invariants are specified in [`actuation_command_pipeline_spec.md`](actuation_command_pipeline_spec.md).

## Notes
- Saturation happens after mixing, so controllers use mixer feedback (`MIXER_FEEDBACK`) for anti-windup (see `interfaces/contracts.md`).

## Open questions
- Controller forms: P vs PI for heading loop, PI for speed/yaw-rate loops
- Anti-windup choice: freeze vs back-calculation (using mixer feedback)
- Limits: $r_{\max}$, $u_{d,\max}$, motor range, slew rates
- Safe behavior at low speed / poor heading observability
- Add tuning procedures and expected plots (link to `docs/ops/`)