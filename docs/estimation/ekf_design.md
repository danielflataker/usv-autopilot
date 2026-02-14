# EKF design (V1)

This document describes the EKF structure used with the V1 process and measurement models.

References:
- Process model: [process_model_v1.md](process_model_v1.md)
- Measurement models: [measurement_models.md](measurement_models.md)
- Frame/units: [architecture.md](../architecture.md)

## Scope and assumptions
- We use an **Extended Kalman Filter (EKF)** because the process model is nonlinear.
- We assume familiarity with state-space notation.
- This document explains EKF terms in plain language so first-time Kalman readers can follow implementation intent.

## Notation
- State: $\vec{x} = [x, y, \psi, v, r, b_g]^{\mathsf T}$
- Input: $\vec{u}_{ach} = [u_s^{ach}, u_d^{ach}]^{\mathsf T}$ (achieved actuation for prediction; compact alias $[u_s,u_d]$ is allowed in equations)
- Measurement: $\vec{z}$
- Process model: $f(\cdot)$
- Measurement model: $h(\cdot)$
- Process noise (models unmodeled process disturbances/model mismatch): $\vec{w}_k \sim \mathcal{N}(\vec{0}, \mathbf{Q}_k)$
- Measurement noise: $\vec{n}_k \sim \mathcal{N}(\vec{0}, \mathbf{R}_k)$
- Angle wrap: $\mathrm{wrap}(\cdot)$ maps to $[-\pi,\pi)$

## Why EKF (not linear KF)
The kinematics contain $\sin(\psi)$ and $\cos(\psi)$, so dynamics are nonlinear:
```math
\vec{x}_{k+1} = f(\vec{x}_k, \vec{u}_k) + \vec{w}_k, \qquad
\vec{z}_k = h(\vec{x}_k) + \vec{n}_k.
```

The EKF linearizes around the current estimate at each step (via Jacobians), then applies Kalman-style covariance propagation and correction.

## Predict step (model-based propagation)
Given posterior estimate $(\hat{\vec{x}}_k, \mathbf{P}_k)$ at time $k$:
```math
\hat{\vec{x}}^-_{k+1} = f(\hat{\vec{x}}_k,\vec{u}_k),
\qquad
\mathbf{P}^-_{k+1} = \mathbf{F}_k\,\mathbf{P}_k\,\mathbf{F}_k^{\mathsf T} + \mathbf{Q}_k,
```
where
```math
\mathbf{F}_k \overset{\text{def}}{=} \left.\frac{\partial f}{\partial \vec{x}}\right|_{\hat{\vec{x}}_k,\vec{u}_k}.
```

Interpretation:
- $\hat{\vec{x}}^-_{k+1}$ is the best guess from physics + inputs alone.
- $\mathbf{P}^-_{k+1}$ is uncertainty after propagation.
- $\mathbf{Q}_k$ injects process-noise uncertainty for unmodeled disturbances (waves/current/model mismatch).

### Jacobian $\mathbf{F}_k$ for V1 (Euler discretization)
With state order $[x,y,\psi,v,r,b_g]$ and sample time $\Delta t$:
```math
\mathbf{F}_k =
\begin{bmatrix}
1 & 0 & -\Delta t\,v\sin\psi & \Delta t\cos\psi & 0 & 0\\
0 & 1 & \Delta t\,v\cos\psi  & \Delta t\sin\psi & 0 & 0\\
0 & 0 & 1 & 0 & \Delta t & 0\\
0 & 0 & 0 & 1-\Delta t/\tau_v & 0 & 0\\
0 & 0 & 0 & 0 & 1-\Delta t/\tau_r & 0\\
0 & 0 & 0 & 0 & 0 & 1
\end{bmatrix},
```
evaluated at $(v,\psi)=(\hat v_k,\hat\psi_k)$.

## Update step (sensor correction)
For a measurement $\vec{z}$ with model $h(\cdot)$:
```math
\tilde{\vec{z}} \overset{\text{def}}{=} \vec{z} - h(\hat{\vec{x}}^-), \qquad
\mathbf{H} \overset{\text{def}}{=} \left.\frac{\partial h}{\partial \vec{x}}\right|_{\hat{\vec{x}}^-}.
```
```math
\mathbf{S} \overset{\text{def}}{=} \mathbf{H}\mathbf{P}^-\mathbf{H}^{\mathsf T} + \mathbf{R}, \qquad
\mathbf{K} \overset{\text{def}}{=} \mathbf{P}^-\mathbf{H}^{\mathsf T}\mathbf{S}^{-1}.
```
```math
\hat{\vec{x}} = \hat{\vec{x}}^- + \mathbf{K}\tilde{\vec{z}}, \qquad
\mathbf{P} = (\mathbf{I}-\mathbf{K}\mathbf{H})\,\mathbf{P}^-.
```

Interpretation:
- Innovation $\tilde{\vec{z}}$ is “what sensors say minus what model predicted sensors should say.”
- $\mathbf{K}$ decides correction strength per state component.
- Large measurement noise in $\mathbf{R}$ means less trust in that sensor channel.

For better numerical stability, Joseph form can be used:
```math
\mathbf{P} = (\mathbf{I}-\mathbf{K}\mathbf{H})\,\mathbf{P}^-\,(\mathbf{I}-\mathbf{K}\mathbf{H})^{\mathsf T} + \mathbf{K}\mathbf{R}\mathbf{K}^{\mathsf T}.
```

### Angle residual handling
Angle residuals must be wrapped, e.g. heading:
```math
\tilde{z}_\psi = \mathrm{wrap}(z_\psi - \hat\psi^-).
```
Without wrapping, a small true difference across $\pm\pi$ can look like a large false residual.

## Measurement Jacobians used in V1

### GNSS position
```math
h_{xy}(\vec{x}) =
\begin{bmatrix}
x\\
y
\end{bmatrix},
\qquad
\mathbf{H}_{xy}=
\begin{bmatrix}
1&0&0&0&0&0\\
0&1&0&0&0&0
\end{bmatrix}.
```

### Gyro yaw-rate
Using $z^{\mathrm{gyro}}_{r} = r + b_g + n_g$:
```math
h_r(\vec{x}) = r + b_g,
\qquad
\mathbf{H}_r=
\begin{bmatrix}
0&0&0&0&1&1
\end{bmatrix}.
```

### Magnetometer heading (optional)
```math
h_\psi(\vec{x}) = \psi,
\qquad
\mathbf{H}_\psi=
\begin{bmatrix}
0&0&1&0&0&0
\end{bmatrix}.
```

## Asynchronous sensors
- Predict runs at control-loop rate using measured $\Delta t$.
- Sensor updates run whenever each measurement arrives (GNSS/mag may be slower than IMU/control loop).
- Apply each update to the latest predicted state/covariance.

## Practical tuning intuition (brief)
- Increase $\mathbf{Q}$ if filter is too confident in model and lags real motion.
- Increase relevant entries of $\mathbf{R}$ if a sensor channel is noisy/outlier-prone.
- Use innovation logs to verify residuals are near-zero mean and roughly match expected variance.

## TODO / Outline
- Define exact $\mathbf{Q}$ and $\mathbf{R}$ parameterization used in code (diagonal vs blocks).
- Add explicit gating rules (innovation/NIS checks) and reject behavior.
- Decide whether/how GNSS COG/speed enters V1 and add corresponding $h(\cdot)$ and $\mathbf{H}$.
