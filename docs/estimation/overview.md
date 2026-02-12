# Estimation overview (V1)

This folder describes the V1 state estimator: what model we use, what sensors we fuse, and how the EKF is structured.

## What the estimator produces
The EKF estimates:
- position $(x,y)$
- heading $\psi$ and yaw-rate $r$
- forward speed $v$
- gyro bias $b_g$

These are consumed by guidance and control.

## Files
- Process model: [process_model_v1.md](process_model_v1.md)
- Measurement models: [measurement_models.md](measurement_models.md)
- EKF equations + Jacobians: [ekf_design.md](ekf_design.md)
- Tuning workflow: [tuning.md](tuning.md)
- Failure modes / health: [failure_modes.md](failure_modes.md)

## V1 philosophy
- Simple, identifiable model first.
- Trust real data more than assumptions: log everything needed to tune $\mathbf{Q}$ and $\mathbf{R}$.
- Handle messy sensors with gating and clear health flags, not fancy models.

## TODO (keep small)
- Define which estimator signals are sent over telemetry (pose + health + optional residual stats)
- Add a short “minimum logging set” for tuning (raw sensors + innovations + state)