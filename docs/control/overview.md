# Control overview (V1)

This folder describes the V1 control stack: track heading and speed, then map to left/right motor commands for a twin-prop boat (no rudder).

Inputs:
- references from [docs/guidance/](../guidance/overview.md)
- state estimates from [docs/estimation/](../estimation/overview.md)

## What control produces (internal)
The controller produces the request-stage actuation vector $\mathbf{q}=[u_s^{req},u_d^{req}]^\top$ in request space:
- average request component $u_s^{req}$ (surge)
- differential request component $u_d^{req}$ (yaw)

Command shaping then produces command-stage terms `u_s_cmd`, `u_d_cmd` in hardware-normalized space.
Allocator and mixer then operate in hardware-normalized space using two bases:
- surge/differential basis: $(u_s,u_d)$
- left/right basis: $(u_L,u_R)$

Final motor mapping is defined in [mixer_and_limits.md](mixer_and_limits.md).

## Files
- [cascaded_heading_yawrate.md](cascaded_heading_yawrate.md) - yaw control: $e_\psi \rightarrow r_d \rightarrow u_d^{req}$
- [speed_controller.md](speed_controller.md) - speed control: $e_v \rightarrow u_s^{req}$
- [command_shaping.md](command_shaping.md) - $\mathbf{q} \rightarrow (u_s^{cmd},u_d^{cmd})$ with scaling/deadband/envelope clamp
- [mixer_and_limits.md](mixer_and_limits.md) - $(u_s^{cmd},u_d^{cmd}) \rightarrow (u_L,u_R)$ + clamp/idle/slew

## V1 control pipeline (short)
1) Guidance provides $\psi_d$ and $v_d$
2) Yaw/speed control computes request stage $\mathbf{q}$
3) Command shaping computes command stage $(u_s^{cmd},u_d^{cmd})$
4) Allocator + mixer + limits produce $(u_L,u_R)$ and feedback $(u_s^{ach},u_d^{ach})$

Detailed stage definitions and naming invariants are specified in [actuation_command_pipeline_spec.md](actuation_command_pipeline_spec.md).

## Notes
- Command clipping can occur at command stage, and motor clipping can occur after mixing in the motor stage.
- Final plant-facing achieved actuation is determined after motor-stage limits/slew, so controllers use `MIXER_FEEDBACK` for anti-windup (see `interfaces/contracts.md`).
- Anti-windup residual is measured in hardware-normalized space: $(u_*^{ach} - u_*^{cmd})$.
- If a controller integrates in request space, map that residual into request space before applying integrator correction.

## Open questions
- Controller forms: P vs PI for heading loop, PI for speed/yaw-rate loops
- Anti-windup choice: freeze vs back-calculation (using mixer feedback)
- Limits: $r_{\max}$, $u_{d,\max}$, motor range, slew rates
- Safe behavior at low speed / poor heading observability
- Add tuning procedures and expected plots (link to `docs/ops/`)
