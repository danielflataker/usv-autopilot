# Control overview

This folder describes how the boat is controlled in V1: reference tracking for heading and speed, then mixing to left/right thrust for a twin-prop boat (no rudder).

The controller takes references from `docs/guidance/` and state estimates from `docs/estimation/`.

## Control outputs
- Total thrust $T$ (surge)
- Differential thrust $\Delta T$ (yaw)

These are mixed into motor commands $(u_L, u_R)$ in `mixer_and_limits.md`.

## Files
- `cascaded_heading_yawrate.md` — yaw control: $e_\psi \rightarrow r_d \rightarrow \Delta T$
- `speed_controller.md` — speed control: $e_v \rightarrow T$
- `mixer_and_limits.md` — $(T,\Delta T) \rightarrow (u_L,u_R)$ + clamps/rate limits

## V1 control pipeline (short)
1) Guidance provides $\psi_d$ and $v_d$
2) Yaw control generates $\Delta T$
3) Speed control generates $T$
4) Mixer + limits produce $(u_L, u_R)$ for the ESCs

## TODO / Outline
- Decide controller forms (P/PI) and anti-windup strategy
- Define limits ($r_{\max}$, $\Delta T_{\max}$, thrust range, slew rates)
- Define safe behavior for low-speed / poor heading observability
- Add bench/water test procedures for tuning (link to `docs/ops/`)