# EKF design (V1)

This document describes the EKF structure used with the V1 process model and measurement models.

References:
- Process model: [process_model_v1.md](process_model_v1.md)
- Measurement models: [measurement_models.md](measurement_models.md)
- Frame/units: [architecture.md](../architecture.md)

## Notation (quick)
- State: $\vec{x} = [x, y, \psi, v, r, b_g]^{\mathsf T}$
- Input: $\vec{u}_{ach} = [u_s^{ach}, u_d^{ach}]^{\mathsf T}$ (achieved actuation for prediction; compact alias $[u_s,u_d]$ is allowed in equations)
- Measurement: $\vec{z}$
- Process noise: $\vec{w}_k \sim \mathcal{N}(\vec{0}, \mathbf{Q}_k)$
- Measurement noise: $\vec{n}_k \sim \mathcal{N}(\vec{0}, \mathbf{R}_k)$
- Angle wrap: $\mathrm{wrap}(\cdot)$ maps to $[-\pi,\pi)$

## Why EKF (not linear KF)
The V1 model is nonlinear because of $\sin(\psi)$ and $\cos(\psi)$ in the kinematics, so we use an EKF:
```math
\vec{x}_{k+1} = f(\vec{x}_k, \vec{u}_k) + \vec{w}_k, \qquad
\vec{z}_k = h(\vec{x}_k) + \vec{n}_k.
```

## Predict step
Given $\hat{\vec{x}}_k$ and covariance $\mathbf{P}_k$:
```math
\hat{\vec{x}}^-_{k+1} = f(\hat{\vec{x}}_k,\vec{u}_k),
\qquad
\mathbf{P}^-_{k+1} = \mathbf{F}_k\,\mathbf{P}_k\,\mathbf{F}_k^{\mathsf T} + \mathbf{Q}_k,
```
where
```math
\mathbf{F}_k \overset{\text{def}}{=} \left.\frac{\partial f}{\partial \vec{x}}\right|_{\hat{\vec{x}}_k,\vec{u}_k}.
```

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

## Measurement update
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

For better numerical stability, the Joseph form can be used:
```math
\mathbf{P} = (\mathbf{I}-\mathbf{K}\mathbf{H})\,\mathbf{P}^-\,(\mathbf{I}-\mathbf{K}\mathbf{H})^{\mathsf T} + \mathbf{K}\mathbf{R}\mathbf{K}^{\mathsf T}.
```

Angle residuals must be wrapped, e.g. for heading:
```math
\tilde{z}_\psi = \mathrm{wrap}(z_\psi - \hat\psi^-).
```

## Measurement Jacobians (V1)

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

## Asynchronous sensors (notes)
- Predict runs at the control loop rate using $\Delta t$.
- GNSS/mag updates happen when new measurements arrive.
- Each measurement update should use the latest predicted state.

## TODO / Outline
- Define $\mathbf{Q}$ and $\mathbf{R}$ parameterization used in code (diagonal vs blocks)
- Add simple gating rules (innovation/NIS checks) and what happens on reject
- Decide how to use GNSS COG/speed (optional) and add $h(\cdot)$ + $\mathbf{H}$ if used