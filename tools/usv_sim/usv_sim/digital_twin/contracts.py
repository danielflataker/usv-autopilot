from __future__ import annotations

from typing import Final

import numpy as np

# Canonical V1 state layout: x = [x, y, psi, v, r, b_g]
IX_X: Final[int] = 0
IX_Y: Final[int] = 1
IX_PSI: Final[int] = 2
IX_V: Final[int] = 3
IX_R: Final[int] = 4
IX_BG: Final[int] = 5

STATE_DIM: Final[int] = 6
INPUT_DIM: Final[int] = 2  # process-model input u = [u_s, u_d] (effective/achieved actuation)

STATE_NAMES: Final[tuple[str, ...]] = ("x", "y", "psi", "v", "r", "b_g")
INPUT_NAMES: Final[tuple[str, ...]] = ("u_s", "u_d")
# Stage semantics: these correspond to effective/achieved actuator effect in the process model.


def as_state_vector(
    x: np.ndarray | list[float] | tuple[float, ...],
    *,
    name: str = "x",
    dtype: np.dtype | type | None = None,
) -> np.ndarray:
    """Return a float state vector with validated shape (STATE_DIM,)."""
    arr = np.asarray(x, dtype=dtype)
    if arr.shape != (STATE_DIM,):
        raise ValueError(f"{name} must have shape ({STATE_DIM},), got {arr.shape}")
    return arr


def as_input_vector(
    u: np.ndarray | list[float] | tuple[float, ...],
    *,
    name: str = "u",
    dtype: np.dtype | type | None = None,
) -> np.ndarray:
    """Return a float input vector with validated shape (INPUT_DIM,)."""
    arr = np.asarray(u, dtype=dtype)
    if arr.shape != (INPUT_DIM,):
        raise ValueError(f"{name} must have shape ({INPUT_DIM},), got {arr.shape}")
    return arr


def as_covariance_matrix(
    P: np.ndarray | list[list[float]],
    *,
    dim: int = STATE_DIM,
    name: str = "P",
    dtype: np.dtype | type | None = None,
) -> np.ndarray:
    """Return a float covariance matrix with validated shape (dim, dim)."""
    arr = np.asarray(P, dtype=dtype)
    if arr.shape != (dim, dim):
        raise ValueError(f"{name} must have shape ({dim}, {dim}), got {arr.shape}")
    return arr
