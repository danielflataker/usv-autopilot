# Cascaded heading / yaw-rate control (V1)

This is the baseline yaw control for a twin-prop boat: an outer loop turns heading error into a desired yaw-rate, and an inner loop tracks yaw-rate using differential thrust.

## Goal
Track a desired heading $\psi_d$ (from LOS) by commanding differential thrust $\Delta T$ (or $u_d$).

## Inputs / outputs
- Inputs: $\psi_d$, $\psi$, $r$ (yaw-rate), $dt$
- Output: $\Delta T$ (or normalized differential command $u_d$)

## Core idea
1) Heading loop: $e_\psi = \mathrm{wrap}(\psi_d - \psi) \rightarrow r_d$  
2) Yaw-rate loop: $e_r = r_d - r \rightarrow \Delta T$

## Outline (what to define)

### 1) Angle handling
- Define $\mathrm{wrap}(\cdot)$ to keep errors in $[-\pi,\pi)$
- Decide sign convention for $\psi$ and $r$ (must match `docs/architecture.md`)

### 2) Outer loop (heading → yaw-rate)
- Choose controller type: P or PI (P is often enough for V1)
- Compute:
  - $e_\psi = \mathrm{wrap}(\psi_d - \psi)$
  - $r_d = \mathrm{sat}(K_{\psi} e_\psi + I_{\psi},\; r_{\max})$
- Optional: gain scheduling vs speed ($K_{\psi}(v)$)

### 3) Inner loop (yaw-rate → differential thrust)
- Choose controller type: P/PI/PID (often PI is fine; gyro gives clean rate)
- Compute:
  - $e_r = r_d - r$
  - $\Delta T = \mathrm{sat}(K_r e_r + I_r - K_d\,\dot r,\; \Delta T_{\max})$  
  (Often no explicit $\dot r$ term; the “D” effect comes from using rate feedback already.)

### 4) Saturation + anti-windup
- Define saturation limits for $r_d$ and $\Delta T$
- Anti-windup strategy (pick one):
  - clamp integrator when saturated
  - back-calculation

### 5) Safety / gating
- Behavior at very low speed (heading from GNSS becomes poor; rely on gyro/EKF)
- What happens if EKF unhealthy: fall back or abort

## Tuning notes (short)
- Start with inner loop first (yaw-rate tracking), then outer loop.
- Keep $r_{\max}$ conservative to avoid aggressive spins.
- Verify sign: step in $\psi_d$ should command $\Delta T$ that turns the boat the correct way.

## TODO
- Pick exact controller forms (P/PI) for both loops
- Decide limits: $r_{\max}$, $\Delta T_{\max}$
- Define integrator update and anti-windup
- Add a simple test procedure + expected plots (link to `ops/bench_tests.md` / `ops/water_test_playbook.md`)