# tools/usv_sim/usv_sim/digital_twin/process_model.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .contracts import (
    IX_BG,
    IX_PSI,
    IX_R,
    IX_V,
    IX_X,
    IX_Y,
    as_input_vector,
    as_state_vector,
)


@dataclass(frozen=True, slots=True)
class ProcessParams:
    """V1 process model parameters.

    tau_v, tau_r: time constants [s]
    k_v, k_r: input gains
    """

    tau_v: float
    tau_r: float
    k_v: float
    k_r: float


def wrap_pi(angle_rad: float) -> float:
    """Wrap angle to [-pi, pi)."""
    return (angle_rad + np.pi) % (2.0 * np.pi) - np.pi


def _process_step_core(
    x: np.ndarray,
    u: np.ndarray,
    dt: float,
    tau_v: float,
    tau_r: float,
    k_v: float,
    k_r: float,
) -> np.ndarray:
    """Core step with only primitive params (easy to Numba later)."""
    # unpack state
    px = float(x[IX_X])
    py = float(x[IX_Y])
    psi = float(x[IX_PSI])
    v = float(x[IX_V])
    r = float(x[IX_R])
    b_g = float(x[IX_BG])

    # unpack achieved actuation inputs: u_ach = [u_s_ach, u_d_ach]
    # Compact algebraic aliases used below: u_s := u_s_ach, u_d := u_d_ach
    u_s_ach = float(u[0])
    u_d_ach = float(u[1])

    cpsi = float(np.cos(psi))
    spsi = float(np.sin(psi))

    # Euler discretization
    px_next = px + dt * v * cpsi
    py_next = py + dt * v * spsi
    psi_next = wrap_pi(psi + dt * r)

    v_dot = -(1.0 / tau_v) * v + k_v * u_s_ach
    r_dot = -(1.0 / tau_r) * r + k_r * u_d_ach

    v_next = v + dt * v_dot
    r_next = r + dt * r_dot

    # bias random walk is modeled via Q in EKF; deterministic step keeps it constant
    b_g_next = b_g

    return np.array(
        [px_next, py_next, psi_next, v_next, r_next, b_g_next], dtype=x.dtype
    )


def process_step(
    x: np.ndarray,
    u: np.ndarray,
    dt: float,
    params: ProcessParams,
    w: Optional[np.ndarray] = None,
) -> np.ndarray:
    """One discrete-time process step for the V1 model.

    Args:
        x: state, shape (6,)
        u: achieved actuation input, shape (2,) where u = [u_s_ach, u_d_ach]
        dt: timestep [s]
        params: model parameters (tau_v, tau_r, k_v, k_r)
        w: optional additive noise, shape (6,) applied after propagation
           (typically only used in simulation; EKF handles this via Q)

    Returns:
        x_next: propagated state, shape (6,)
    """
    x = as_state_vector(x, name="x", dtype=float)
    u = as_input_vector(u, name="u", dtype=float)
    if dt <= 0.0:
        raise ValueError("dt must be > 0")
    if not isinstance(params, ProcessParams):
        raise TypeError(f"params must be ProcessParams, got {type(params).__name__}")
    tau_v = float(params.tau_v)
    tau_r = float(params.tau_r)
    k_v = float(params.k_v)
    k_r = float(params.k_r)
    if not np.isfinite(tau_v) or tau_v <= 0.0:
        raise ValueError("params.tau_v must be finite and > 0")
    if not np.isfinite(tau_r) or tau_r <= 0.0:
        raise ValueError("params.tau_r must be finite and > 0")
    if not np.isfinite(k_v):
        raise ValueError("params.k_v must be finite")
    if not np.isfinite(k_r):
        raise ValueError("params.k_r must be finite")

    x_next = _process_step_core(
        x=x,
        u=u,
        dt=float(dt),
        tau_v=tau_v,
        tau_r=tau_r,
        k_v=k_v,
        k_r=k_r,
    )

    if w is not None:
        w = np.asarray(w, dtype=x_next.dtype)
        if w.shape != (6,):
            raise ValueError(f"w must have shape (6,), got {w.shape}")
        x_next = x_next + w
        x_next[IX_PSI] = wrap_pi(float(x_next[IX_PSI]))

    return x_next
