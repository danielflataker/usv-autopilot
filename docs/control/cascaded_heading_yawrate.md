# Cascaded heading / yaw-rate control (V1)

Baseline yaw control for a twin-prop boat: an outer loop turns heading error into a desired yaw-rate, and an inner loop tracks yaw-rate using the normalized differential request $u_d^{req}$.

## Goal
Track a desired heading $\psi_d$ (from LOS) by commanding $u_d^{req}$.

## Inputs / outputs
- Inputs: $\psi_d$, $\psi$, $r$, $\Delta t$
- Output: $u_d^{req}$ (normalized differential request; command stage is produced later by command shaping)

## Core idea
1) Heading loop: $e_\psi = \mathrm{wrap}(\psi_d - \psi) \rightarrow r_d$  
2) Yaw-rate loop: $e_r = r_d - r \rightarrow u_d^{req}$

## Outline (what to define)

### 1) Angle handling
- Use canonical `wrap`, `psi`, and `r` conventions from [architecture.md](../architecture.md)

### 2) Outer loop (heading $\rightarrow$ yaw-rate)
- Choose controller type: P or PI (P is often enough for V1)
- Compute:
  - $e_\psi = \mathrm{wrap}(\psi_d - \psi)$
  - $r_d = \mathrm{sat}(K_{\psi} e_\psi + I_{\psi},\; r_{\max})$
- Optional: gain scheduling vs speed $K_{\psi}(v)$

### 3) Inner loop (yaw-rate $\rightarrow$ differential command)
- Choose controller type: P/PI (PI is typical)
- Compute:
  - $e_r = r_d - r$
  - $u_d^{req} = K_r e_r + I_r$
- Note: a separate D-term is usually not needed because rate feedback ($r$) is already used.

### 4) Saturation + anti-windup
- Define limits for $r_d$ and request-stage behavior for $u_d^{req}$
- Anti-windup strategy (pick one):
  - freeze/clamp integrator when saturated
  - back-calculation

### 5) Safety / gating
- Very low speed: heading observability can be poor (GNSS COG unreliable); rely on gyro/EKF
- If EKF unhealthy: fall back or abort (TBD)

## Tuning notes (short)
- Tune inner loop first (yaw-rate tracking), then outer loop.
- Keep $r_{\max}$ conservative to avoid aggressive spins.
- Verify sign: a positive step in $\psi_d$ should produce $u_d^{req}$ that turns the boat the correct way.

## Saturation + anti-windup (V1)

Actuator saturation happens *after mixing* (motor limits on $u_L,u_R$), so the controllers must use mixer feedback for anti-windup.

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

## TODO
- Pick exact controller forms (P/PI) for both loops
- Decide limits: $r_{\max}$, $u_{d,\max}$
- Define integrator update and anti-windup
- Add a simple test procedure + expected plots (link `ops/bench_tests.md` / `ops/water_test_playbook.md`)
