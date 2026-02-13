from __future__ import annotations

import numpy as np

from usv_sim.digital_twin.process_model import ProcessParams
from .base import DEFAULT_PARAMS, Scenario, X_PSI


def make_step_us(
    *,
    dt: float,
    T: float,
    u_s0: float,
    u_s1: float,
    t_step: float,
    u_d: float = 0.0,
    x0: np.ndarray | None = None,
    params: ProcessParams | None = None,
) -> Scenario:
    """Step in u_s at t_step. u_d held constant. Returns U[:,0]=u_s, U[:,1]=u_d."""
    if dt <= 0.0:
        raise ValueError("dt must be > 0")
    if T <= 0.0:
        raise ValueError("T must be > 0")

    N = int(np.ceil(T / dt))
    t = np.arange(N, dtype=np.float64) * float(dt)

    U = np.empty((N, 2), dtype=np.float64)
    U[:, 0] = np.where(t >= float(t_step), float(u_s1), float(u_s0))
    U[:, 1] = float(u_d)

    if x0 is None:
        x0 = np.zeros(6, dtype=np.float64)
        x0[X_PSI] = 0.0
    else:
        x0 = np.asarray(x0, dtype=np.float64)
        if x0.shape != (6,):
            raise ValueError(f"x0 must have shape (6,), got {x0.shape}")

    return Scenario(
        name="step_us",
        dt=float(dt),
        U=U,
        x0=x0,
        params=params or DEFAULT_PARAMS,
    )
