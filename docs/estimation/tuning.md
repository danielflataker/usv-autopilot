# Tuning (estimation)

This page is about tuning the EKF in practice: choosing $\mathbf{Q}$ and $\mathbf{R}$, and adding basic gating.
Keep this iterative. Start with conservative values, then tune from logs.

References:
- [process_model_v1.md](process_model_v1.md)
- [measurement_models.md](measurement_models.md)
- [ekf_design.md](ekf_design.md)

## What gets tuned
- Measurement noise $\mathbf{R}$ (sensor trust level)
- Process noise $\mathbf{Q}$ (model trust level; captures unmodeled process disturbances/model mismatch)
- Gating thresholds (reject outliers)

## Starting point (safe defaults)
- Set $\mathbf{R}$ based on sensor specs first, then adjust using logged residuals
- Keep $\mathbf{Q}$ large enough that the filter is not “overconfident”, especially for $v$ and $r$
- Bias noise $Q_{bb}$ should be small but nonzero (models slow drift)

## Practical workflow
1) Log raw measurements + EKF outputs + innovations
2) Check innovations: are they near zero-mean? too large? too small?
3) Adjust $\mathbf{R}$ and $\mathbf{Q}$, one change at a time
4) Re-run the same test (repeatable segments)

## TODO / Outline

### Measurement noise $\mathbf{R}$
- GNSS position: choose variance from reported accuracy / empirical scatter
- Gyro: choose variance from datasheet + measured noise on bench
- Mag/COG (if used): treat as coarse, large variance, and gate hard

### Process noise $\mathbf{Q}$
- Model mismatch lives here (waves, current, thrust nonlinearity)
- Decide which states get most process noise variance (typically $v$, $r$, and $b_g$)
- Decide how $\mathbf{Q}$ scales with $\Delta t$

### Gating / outlier rejection
- Use innovation test (NIS) per measurement type
- Reject GNSS jumps and stale heading updates
- Log rejects as events (so tuning is traceable)

### What to plot from logs
- Innovations / residuals over time
- NIS values + accept/reject decisions
- State covariance diagonals (sanity: not collapsing to zero or exploding)

## Open questions
- Is adaptive $\mathbf{R}$ for GNSS needed based on reported accuracy/HDOP?
- Is a simple “EKF unhealthy” criterion needed for failsafe decisions?
