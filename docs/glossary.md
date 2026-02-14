# Glossary

Quick reference for shared vocabulary across the docs. Math uses $\,\cdot\,$, code/log field names use backticks.

## Conventions
- `t_us`: monotonic timestamp in microseconds (code/log field name).
- Units: SI (m, rad, m/s, rad/s) unless explicitly stated.
- $(x,y)$: local navigation position (frame defined in [architecture.md](architecture.md)).
- $\psi$: heading/yaw angle.
- $\mathrm{wrap}(\cdot)$: wrap angle differences (e.g. to $[-\pi,\pi)$).
- For control commands, use superscripts to show stage in the pipeline:
  - $u_*^{cmd}$: command requested by controller.
  - $u_*^{ach}$: command achieved after allocator/mixer/limits.
  - $u_*^{*}$: raw/unclamped controller output (before saturation/anti-windup logic).
- In code/log field names, stage uses explicit suffixes consistently:
  - command stage: `u_s_cmd`, `u_d_cmd`
  - achieved stage: `u_s_ach`, `u_d_ach`
  - raw (pre-saturation) stage: `u_s_raw`, `u_d_raw`

## Estimation symbols (EKF)
State (V1): $\vec{x} = [x, y, \psi, v, r, b_g]^{\mathsf T}$
- $v$: surge speed estimate [m/s]
- $r$: yaw rate [rad/s]
- $b_g$: gyro bias (slow drift; modeled as random walk) [rad/s]
- $\mathbf{Q}$: process noise covariance
- $\mathbf{R}$: measurement noise covariance

| Math | Code name |
|---|---|
| $x,y,\psi,v,r,b_g$ | `x,y,psi,v,r,b_g` |
| $\mathbf{Q}$ | `Q` |
| $\mathbf{R}$ | `R` |

## Guidance + control symbols (math ↔ code)
Key relations:
- $e_v = v_d - v$
- $e_r = r_d - r$
- $u_s = 0.5(u_L + u_R)$, $u_d = 0.5(u_R - u_L)$
- $u_L = u_s - u_d$, $u_R = u_s + u_d$

| Math | Code name | Meaning / unit |
|---|---|---|
| $v_{\mathrm{seg}}$ | `v_seg` | segment target speed [m/s] |
| $v_d$ | `v_d` | desired speed setpoint after caps+ramp [m/s] |
| $\psi_d$ | `psi_d` | desired heading from LOS [rad] |
| $e_y$ | `e_y` | cross-track error [m] |
| $e_\psi$ | `e_psi` | heading error (wrapped) [rad] |
| $r_d$ | `r_d` | desired yaw rate [rad/s] |
| $e_r$ | `e_r` | yaw-rate error [rad/s] |
| $e_v$ | `e_v` | speed error [m/s] |
| $u_L$ | `u_L` | left motor command (normalized) |
| $u_R$ | `u_R` | right motor command (normalized) |
| $u_s$ | `u_s` | average input (normalized) |
| $u_d$ | `u_d` | differential input (normalized) |
| $u_s^{cmd},u_d^{cmd}$ | `u_s_cmd,u_d_cmd` in `actuator_cmd_t` | commanded average/differential input |
| $u_s^{ach},u_d^{ach}$ | `u_s_ach,u_d_ach` | achieved average/differential input after limits |
| $u_s^{*},u_d^{*}$ | `u_s_raw,u_d_raw` | raw controller outputs before clamp/anti-windup |
| $s_L,s_R,s_{any}$ | `sat_L,sat_R,sat_any` | per-motor/any saturation indicators |

## Cross-domain actuator mapping (firmware ↔ sim)

To make simulator/hardware swap straightforward, we standardize the stage names and allow one explicit legacy alias in process-model math:

| Stage | Canonical math | Firmware/log field names | Simulator/process-model names |
|---|---|---|---|
| Controller command | $u_s^{cmd},u_d^{cmd}$ | `u_s_cmd`,`u_d_cmd` | used as upstream input to allocator/mixer logic |
| Achieved actuation | $u_s^{ach},u_d^{ach}$ | `u_s_ach`,`u_d_ach` | `u_s_ach`,`u_d_ach` (`u_s`,`u_d` accepted only as compact algebraic aliases) |

Sign convention reminder:
- Positive $u_d$ means right motor command exceeds left motor command ($u_R > u_L$), i.e. in mixer form $u_R=u_s+u_d$, $u_L=u_s-u_d$.

## Sensors and measurements
- GNSS: Global Navigation Satellite System
  - `z_gnss_xy`: GNSS position in local frame
  - GS: ground speed (speed over ground)
  - COG: course over ground (direction of motion over ground)
- IMU: Inertial Measurement Unit
  - gyro `z_gyro_r`: measured yaw rate
  - accel `z_acc`: measured acceleration (logged in V1; not necessarily used in estimation yet)
- Magnetometer (optional): heading measurement `z_mag_psi` (EMI dependent)

## Logging terms
- `timeseries.bin`: high-rate binary time series
- `events.jsonl`: sparse event log
- `meta.json`: session metadata (`git_sha`, `git_dirty`, params snapshot, …)

## Abbreviations
- EKF: Extended Kalman Filter
- LOS: Line-Of-Sight guidance
- PID: Proportional–Integral–Derivative controller
- RTOS: Real-Time Operating System
- ESC: Electronic Speed Controller
- SD: Secure Digital (storage)
- SiK: serial telemetry radio modules
