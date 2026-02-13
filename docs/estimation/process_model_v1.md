# V1 process model

This is the baseline process model used by the EKF in V1. It’s deliberately simple: planar motion, lumped 1st-order dynamics for forward speed and yaw-rate, and a gyro bias state.

## Assumptions
- Planar motion (roll/pitch ignored).
- Forward speed $v$ is along heading $\psi$ (no sway state in V1).
- Motor commands are normalized (e.g. $u_L,u_R \in [-1,1]$).
- Unmodelled effects (waves, current, thrust nonlinearity) are handled as process noise.

Coordinate frames and sign conventions are defined in [architecture.md](../architecture.md).

## State
```math
\vec{x} =
\begin{bmatrix}
x & y & \psi & v & r & b_g
\end{bmatrix}^{\mathsf T},
```
where $b_g$ is gyro bias for yaw-rate (random walk in V1).

## Inputs (motor commands)
Per-motor commands:
- $u_L$: left motor command
- $u_R$: right motor command

We use average + difference:
$$
u_s = \tfrac12(u_L + u_R), \qquad
u_d = \tfrac12(u_R - u_L).
$$

Process input vector:
```math
\vec{u} =
\begin{bmatrix}
u_s \\
u_d
\end{bmatrix}.
```

Inverse mapping (used by the mixer):
```math
u_L = u_s - u_d, \qquad
u_R = u_s + u_d.
```

## Continuous-time dynamics
Kinematics:
```math
\dot x = v\cos\psi, \qquad
\dot y = v\sin\psi, \qquad
\dot\psi = r.
```

Lumped 1st-order dynamics:
```math
\dot v = -\tfrac{1}{\tau_v}v + k_v u_s + w_v, \qquad
\dot r = -\tfrac{1}{\tau_r}r + k_r u_d + w_r, \qquad
\dot b_g = w_b.
```

Compact form (for EKF notation):
```math
\dot{\vec{x}} = f(\vec{x},\vec{u}) + \vec{w}, \qquad
\vec{w} =
\begin{bmatrix}
0 & 0 & 0 & w_v & w_r & w_b
\end{bmatrix}^{\mathsf T}.
```

Here $\tau_v,\tau_r,k_v,k_r$ are parameters, and $w_\star$ captures model mismatch.

## Discrete-time model (Euler)
With sample time $\Delta t$:
```math
x_{k+1} = x_k + \Delta t\, v_k\cos\psi_k,
\qquad
y_{k+1} = y_k + \Delta t\, v_k\sin\psi_k,
\qquad
\psi_{k+1} = \mathrm{wrap}\!\left(\psi_k + \Delta t\,r_k\right),
```
```math
v_{k+1} = v_k + \Delta t\left(-\tfrac{1}{\tau_v}v_k + k_v u_{s,k}\right),
\qquad
r_{k+1} = r_k + \Delta t\left(-\tfrac{1}{\tau_r}r_k + k_r u_{d,k}\right),
\qquad
b_{g,k+1} = b_{g,k} + w_{b,k}.
```

Process noise is applied as
```math
\vec{x}_{k+1} = f(\vec{x}_k,\vec{u}_k) + \vec{w}_k,
\qquad
\vec{w}_k \sim \mathcal N(\vec{0},\mathbf{Q}_k).
```

## Parameters and identification
- $\tau_v,\tau_r$: time constants for surge and yaw-rate response
- $k_v,k_r$: input gains from $(u_s,u_d)$ to $(\dot v,\dot r)$

These are intended to be identified on-water using simple tests (step, turn, zig-zag) in `TESTS` mode.

## Notes
- The model is intentionally “wrong but useful”. Tuning $\mathbf{Q}$ is expected.
- If reverse thrust is not available, clamp/rules belong in the actuator layer, not here.

## Upgrade path (later)
We might want to add slowly varying current/drift as extra states, e.g. $(v_{c,x}, v_{c,y})$, before moving to a higher-order 3DOF model.