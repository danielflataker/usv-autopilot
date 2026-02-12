# Measurement models (V1)

This file defines the measurement models used by the EKF in V1.

General form:
$$
\vec{z}_k = h(\vec{x}_k) + \vec{n}_k, \qquad \vec{n}_k \sim \mathcal{N}(\vec{0},\mathbf{R}_k).
$$

Notes on notation:
- Use $\vec{x}$ for state, $\vec{u}$ for process input.
- Use $\vec{n}$ for measurement noise (to avoid confusion with the speed state $v$).
- Angle differences must be wrapped to $[-\pi,\pi)$.

Frame and units conventions are defined in [architecture.md](../architecture.md).

## Sensors in V1

### GNSS position (local $x,y$)
GNSS position is assumed to be provided in the local navigation frame (after projection from lat/lon):
$$
\vec{z}^{\mathrm{gnss}}_{xy} =
\begin{bmatrix}
x \\
y
\end{bmatrix}
+
\vec{n}_{xy}.
$$

Typical use:
- Update whenever a new GNSS fix arrives (asynchronous vs control loop).

### IMU gyro (yaw-rate)
Gyro $z$ measures yaw-rate with additive bias:
$$
z^{\mathrm{gyro}}_{r} = r + b_g + n_g.
$$

Comments:
- $b_g$ is part of the state (random walk in the process model, models slow drift).
- $n_g$ is gyro measurement noise.

### Magnetometer heading (might leave out for V1)
When a magnetometer heading estimate is available:
$$
z^{\mathrm{mag}}_{\psi} = \psi + n_{\psi}.
$$

Important:
- Innovation must be wrapped:
  $$
  \nu_\psi = \mathrm{wrap}(z^{\mathrm{mag}}_{\psi} - \hat{\psi}^-).
  $$

### GNSS speed and course (might leave out for V1)
Some GNSS receivers provide ground speed and course-over-ground (COG). These can be used as coarse helper measurements, but only when moving above a threshold $v > v_{\min}$.

Speed (approximate):
$$
z^{\mathrm{gnss}}_{v} \approx v + n_v.
$$

Course (approximate heading):
$$
z^{\mathrm{gnss}}_{\mathrm{cog}} \approx \psi + n_{\psi,\mathrm{cog}}.
$$

Notes:
- Ground speed and COG are affected by current/wind and may deviate from body-frame surge behavior.
- We treat these with relatively large covariance in $\mathbf{R}$, and gate on $v > v_{\min}$.

## TODO / Outline
- Define recommended measurement rates for each sensor (typical, not hard requirements)
- Define gating rules (GNSS jump rejection, min speed for COG)
- Decide whether telemetry/logging should carry raw GNSS lat/lon in addition to local $x,y$
- Add Jacobians $\mathbf{H}$ for each measurement model (or link to `ekf_design.md`)