from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Tuple

import numpy as np

from ..contracts import (
    IX_BG,
    IX_PSI,
    IX_R,
    IX_V,
    IX_X,
    IX_Y,
    STATE_DIM,
    as_covariance_matrix,
    as_input_vector,
    as_state_vector,
)
from ..process_model import ProcessParams, process_step, wrap_pi

ResidualFn = Callable[[np.ndarray, np.ndarray], np.ndarray]
MeasFn = Callable[[np.ndarray], np.ndarray]
JacobianFn = Callable[[np.ndarray], np.ndarray]


@dataclass(frozen=True, slots=True)
class UpdateResult:
    innovation: np.ndarray
    S: np.ndarray
    K: np.ndarray


@dataclass(slots=True)
class EkfState:
    """Mutable EKF state container for x and P."""

    x: np.ndarray
    P: np.ndarray

    def __post_init__(self) -> None:
        self.x = as_state_vector(self.x, name="x", dtype=float)
        self.P = as_covariance_matrix(self.P, dim=STATE_DIM, name="P", dtype=float)

    def copy(self) -> "EkfState":
        return EkfState(x=self.x.copy(), P=self.P.copy())


@dataclass(frozen=True, slots=True)
class MeasurementModel:
    """Measurement model bundle: z_hat = h(x), H = dh/dx, and residual function."""

    name: str
    h: MeasFn
    H: JacobianFn
    residual: ResidualFn


def residual_identity(z: np.ndarray, z_hat: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=float).reshape(-1)
    z_hat = np.asarray(z_hat, dtype=float).reshape(-1)
    if z.shape != z_hat.shape:
        raise ValueError(f"z and z_hat must have the same shape, got {z.shape} and {z_hat.shape}")
    return z - z_hat


def residual_heading(z: np.ndarray, z_hat: np.ndarray) -> np.ndarray:
    res = residual_identity(z, z_hat)
    if res.shape != (1,):
        raise ValueError(f"heading residual expects shape (1,), got {res.shape}")
    res[0] = wrap_pi(float(res[0]))
    return res


def h_gnss_xy(x: np.ndarray) -> np.ndarray:
    x = as_state_vector(x, dtype=float)
    return np.array([x[IX_X], x[IX_Y]], dtype=float)


def H_gnss_xy(_x: np.ndarray) -> np.ndarray:
    H = np.zeros((2, STATE_DIM), dtype=float)
    H[0, IX_X] = 1.0
    H[1, IX_Y] = 1.0
    return H


def h_gyro_r(x: np.ndarray) -> np.ndarray:
    x = as_state_vector(x, dtype=float)
    return np.array([x[IX_R] + x[IX_BG]], dtype=float)


def H_gyro_r(_x: np.ndarray) -> np.ndarray:
    H = np.zeros((1, STATE_DIM), dtype=float)
    H[0, IX_R] = 1.0
    H[0, IX_BG] = 1.0
    return H


def h_mag_psi(x: np.ndarray) -> np.ndarray:
    x = as_state_vector(x, dtype=float)
    return np.array([x[IX_PSI]], dtype=float)


def H_mag_psi(_x: np.ndarray) -> np.ndarray:
    H = np.zeros((1, STATE_DIM), dtype=float)
    H[0, IX_PSI] = 1.0
    return H


gnss_xy_model = MeasurementModel(
    name="gnss_xy",
    h=h_gnss_xy,
    H=H_gnss_xy,
    residual=residual_identity,
)

gyro_r_model = MeasurementModel(
    name="gyro_r",
    h=h_gyro_r,
    H=H_gyro_r,
    residual=residual_identity,
)

mag_psi_model = MeasurementModel(
    name="mag_psi",
    h=h_mag_psi,
    H=H_mag_psi,
    residual=residual_heading,
)


def jacobian_F(x: np.ndarray, dt: float, params: ProcessParams) -> np.ndarray:
    """Analytic process Jacobian for the V1 Euler-discretized process model."""
    x = as_state_vector(x, dtype=float)
    if dt <= 0.0:
        raise ValueError("dt must be > 0")
    if not isinstance(params, ProcessParams):
        raise TypeError(f"params must be ProcessParams, got {type(params).__name__}")

    psi = float(x[IX_PSI])
    v = float(x[IX_V])

    cpsi = float(np.cos(psi))
    spsi = float(np.sin(psi))

    F = np.eye(STATE_DIM, dtype=float)
    F[IX_X, IX_PSI] = -dt * v * spsi
    F[IX_X, IX_V] = dt * cpsi
    F[IX_Y, IX_PSI] = dt * v * cpsi
    F[IX_Y, IX_V] = dt * spsi
    F[IX_PSI, IX_R] = dt
    F[IX_V, IX_V] = 1.0 - dt / float(params.tau_v)
    F[IX_R, IX_R] = 1.0 - dt / float(params.tau_r)
    return F


def predict_step(
    x: np.ndarray,
    P: np.ndarray,
    u: np.ndarray,
    dt: float,
    params: ProcessParams,
    Q: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """EKF predict step: x^- = f(x,u), P^- = F P F^T + Q."""
    x = as_state_vector(x, dtype=float)
    P = as_covariance_matrix(P, dim=STATE_DIM, name="P", dtype=float)
    u = as_input_vector(u, name="u", dtype=float)
    Q = as_covariance_matrix(Q, dim=STATE_DIM, name="Q", dtype=float)
    if dt <= 0.0:
        raise ValueError("dt must be > 0")

    F = jacobian_F(x, dt, params)
    x_pred = process_step(x=x, u=u, dt=dt, params=params, w=None)
    P_pred = F @ P @ F.T + Q
    P_pred = 0.5 * (P_pred + P_pred.T)
    return x_pred, P_pred, F


class ExtendedKalmanFilter:
    """V1 EKF wrapper around process and measurement model components."""

    def __init__(
        self,
        *,
        params: ProcessParams,
        Q: np.ndarray,
        x0: Optional[np.ndarray] = None,
        P0: Optional[np.ndarray] = None,
        joseph_form: bool = True,
    ) -> None:
        if not isinstance(params, ProcessParams):
            raise TypeError(f"params must be ProcessParams, got {type(params).__name__}")

        self.params = params
        self.Q = as_covariance_matrix(Q, dim=STATE_DIM, name="Q", dtype=float)
        self.joseph_form = bool(joseph_form)

        if x0 is None:
            x0 = np.zeros(STATE_DIM, dtype=float)
        if P0 is None:
            P0 = np.eye(STATE_DIM, dtype=float)
        self.state = EkfState(x=x0, P=P0)

    @property
    def x(self) -> np.ndarray:
        return self.state.x

    @property
    def P(self) -> np.ndarray:
        return self.state.P

    def set_process_noise(self, Q: np.ndarray) -> None:
        self.Q = as_covariance_matrix(Q, dim=STATE_DIM, name="Q", dtype=float)

    def predict(self, u: np.ndarray, dt: float) -> np.ndarray:
        u = as_input_vector(u, name="u", dtype=float)
        x_pred, P_pred, _F = predict_step(
            x=self.state.x,
            P=self.state.P,
            u=u,
            dt=dt,
            params=self.params,
            Q=self.Q,
        )
        self.state.x = x_pred
        self.state.P = P_pred
        return self.state.x

    def update(self, z: np.ndarray, R: np.ndarray, model: MeasurementModel) -> UpdateResult:
        z = np.asarray(z, dtype=float).reshape(-1)
        z_hat = np.asarray(model.h(self.state.x), dtype=float).reshape(-1)
        m = int(z.shape[0])
        if z_hat.shape != (m,):
            raise ValueError(f"{model.name}: h(x) shape {z_hat.shape} does not match z shape {z.shape}")

        H = np.asarray(model.H(self.state.x), dtype=float)
        if H.shape != (m, STATE_DIM):
            raise ValueError(f"{model.name}: H must have shape ({m}, {STATE_DIM}), got {H.shape}")

        R = as_covariance_matrix(R, dim=m, name="R", dtype=float)
        innovation = np.asarray(model.residual(z, z_hat), dtype=float).reshape(-1)
        if innovation.shape != (m,):
            raise ValueError(
                f"{model.name}: residual must return shape ({m},), got {innovation.shape}"
            )

        P = self.state.P
        S = H @ P @ H.T + R
        PHt = P @ H.T
        K = np.linalg.solve(S, PHt.T).T

        x_upd = self.state.x + K @ innovation
        x_upd[IX_PSI] = wrap_pi(float(x_upd[IX_PSI]))

        if self.joseph_form:
            I = np.eye(STATE_DIM, dtype=float)
            KH = K @ H
            P_upd = (I - KH) @ P @ (I - KH).T + K @ R @ K.T
        else:
            P_upd = (np.eye(STATE_DIM, dtype=float) - K @ H) @ P

        self.state.x = as_state_vector(x_upd, name="x", dtype=float)
        self.state.P = 0.5 * (P_upd + P_upd.T)
        return UpdateResult(innovation=innovation, S=S, K=K)

    def update_gnss_xy(self, z_xy: np.ndarray, R_xy: np.ndarray) -> UpdateResult:
        return self.update(z=z_xy, R=R_xy, model=gnss_xy_model)

    def update_gyro_r(self, z_r: np.ndarray, R_r: np.ndarray) -> UpdateResult:
        return self.update(z=z_r, R=R_r, model=gyro_r_model)

    def update_mag_psi(self, z_psi: np.ndarray, R_psi: np.ndarray) -> UpdateResult:
        return self.update(z=z_psi, R=R_psi, model=mag_psi_model)


__all__ = [
    "EkfState",
    "ExtendedKalmanFilter",
    "UpdateResult",
    "MeasurementModel",
    "gnss_xy_model",
    "gyro_r_model",
    "mag_psi_model",
    "residual_identity",
    "residual_heading",
    "jacobian_F",
    "predict_step",
]
