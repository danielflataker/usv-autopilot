# Failure modes (estimation)

This page lists likely failure modes for the V1 estimator and what to do about them.
Keep it lightweight.

## What can go wrong (V1)

- **GNSS dropouts / no fix**
  - Symptom: no position updates, stale $x,y$
  - Notes: estimator will drift using process model only

- **GNSS jumps / multipath**
  - Symptom: sudden large position residuals
  - Notes: should be handled by gating / outlier reject

- **Bad heading observability at low speed**
  - Symptom: GNSS COG becomes noisy; heading updates become unreliable
  - Notes: avoid using COG below $v_{\min}$

- **Gyro bias drift**
  - Symptom: yaw-rate offset; heading slowly drifts if not corrected
  - Notes: bias state + reasonable $Q_{bb}$ helps

- **Magnetometer disturbance (if used)**
  - Symptom: heading spikes near motors/wiring
  - Notes: treat as optional, gate aggressively, or disable

- **Time / timestamp issues**
  - Symptom: wrong $\Delta t$, out-of-order measurements
  - Notes: can silently ruin the filter

## Detection signals (placeholder)
- Innovation magnitude / NIS for GNSS and heading
- “stale sensor” timers (no updates in $T$ seconds)
- EKF health flag (divergence / covariance blow-up)

## TODO / Outline
- Define minimal health flags to expose over telemetry and log as events
- Add recommended gating thresholds (after first real logs)
- Define fallback behavior (ignore measurement, increase $Q$, or abort) per sensor type