from __future__ import annotations

import numpy as np

from usv_sim.digital_twin.process_model import ProcessParams
from .base import Scenario, DEFAULT_PARAMS


def make_constant_turn(
    *,
    dt: float,
    T: float,
    u_s_ach: float,
    u_d_ach: float,
    x0: np.ndarray | None = None,
    params: ProcessParams | None = None,
) -> Scenario:
    """Constant u_s_ach and u_d_ach (achieved inputs). Often yields a curved path."""
    if dt <= 0.0:
        raise ValueError("dt must be > 0")
    if T <= 0.0:
        raise ValueError("T must be > 0")

    N = int(np.ceil(T / dt))
    U = np.empty((N, 2), dtype=np.float64)
    U[:, 0] = float(u_s_ach)
    U[:, 1] = float(u_d_ach)

    if x0 is None:
        x0 = np.zeros(6, dtype=np.float64)
    else:
        x0 = np.asarray(x0, dtype=np.float64)
        if x0.shape != (6,):
            raise ValueError(f"x0 must have shape (6,), got {x0.shape}")

    return Scenario(
        name="constant_turn",
        dt=float(dt),
        U=U,
        x0=x0,
        params=params or DEFAULT_PARAMS,
    )
