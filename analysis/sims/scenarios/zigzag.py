from __future__ import annotations

import numpy as np

from usv_sim.digital_twin.process_model import ProcessParams
from .base import DEFAULT_PARAMS, Scenario


def make_zigzag_ud(
    *,
    dt: float,
    T: float,
    u_s_ach: float,
    u_d_ach_amp: float,
    period: float,
    x0: np.ndarray | None = None,
    params: ProcessParams | None = None,
) -> Scenario:
    """Square-wave in u_d_ach (left/right), constant u_s_ach. Returns U[:,0]=u_s_ach, U[:,1]=u_d_ach."""
    if dt <= 0.0:
        raise ValueError("dt must be > 0")
    if T <= 0.0:
        raise ValueError("T must be > 0")
    if period <= 0.0:
        raise ValueError("period must be > 0")

    N = int(np.ceil(T / dt))
    t = np.arange(N, dtype=np.float64) * float(dt)

    U = np.empty((N, 2), dtype=np.float64)
    U[:, 0] = float(u_s_ach)
    phase = np.sin(2.0 * np.pi * t / float(period))
    U[:, 1] = np.where(phase >= 0.0, float(u_d_ach_amp), -float(u_d_ach_amp))

    if x0 is None:
        x0 = np.zeros(6, dtype=np.float64)
    else:
        x0 = np.asarray(x0, dtype=np.float64)
        if x0.shape != (6,):
            raise ValueError(f"x0 must have shape (6,), got {x0.shape}")

    return Scenario(
        name="zigzag_ud",
        dt=float(dt),
        U=U,
        x0=x0,
        params=params or DEFAULT_PARAMS,
    )
