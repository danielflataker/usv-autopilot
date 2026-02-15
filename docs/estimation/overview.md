# Estimation overview (V1)

This folder describes the V1 state estimator: model choice, fused sensors, and EKF structure.

Assumptions for this documentation:
- Comfort with state-space models (`x`, `u`, `y`) and Jacobians is assumed.
- Newness to Kalman filtering is acceptable.

## One-minute mental model
Think of the estimator as a continuous correction loop:
1. Predict where the boat should be now using the process model + motor commands.
2. Compare that prediction to available sensor readings.
3. Correct the state using weighted residuals (trusting cleaner sensors more).
4. Repeat at every timestep / sensor arrival.

In EKF language, this is the predict/update cycle around a nonlinear model.

## What the estimator outputs
The V1 EKF estimates:
- position $(x,y)$
- heading $\psi$ and yaw-rate $r$
- forward speed $v$
- gyro bias $b_g$

These are consumed by guidance and control. The goal is not to make every estimate “perfect,” but to provide a stable and physically consistent state for downstream loops.

## What each document covers
- Process model (`f`): [process_model_v1.md](process_model_v1.md)
- Measurement models (`h`): [measurement_models.md](measurement_models.md)
- EKF predict/update math and Jacobians: [ekf_design.md](ekf_design.md)
- Practical tuning workflow (`Q`, `R`, gating): [tuning.md](tuning.md)
- Failure modes and health behavior: [failure_modes.md](failure_modes.md)

## V1 design philosophy
- Start with a simple model that is easy to identify and debug.
- Use logs + innovation statistics to tune, rather than overfitting a complicated model early.
- Handle real-world sensor messiness with explicit gating and health flags.

## Reading order (recommended)
For readers new to Kalman filtering:
1. Read this file.
2. Read [process_model_v1.md](process_model_v1.md) to understand what “prediction” means physically.
3. Read [measurement_models.md](measurement_models.md) to understand what sensors can correct.
4. Read [ekf_design.md](ekf_design.md) for the exact EKF equations used.
5. Read [tuning.md](tuning.md) before changing covariance values.

## TODO (keep small)
- Define which estimator signals are sent over telemetry (pose + health + optional residual stats).
- Add a short “minimum logging set” for tuning (raw sensors + innovations + state).
