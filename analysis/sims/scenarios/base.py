from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import numpy.typing as npt

from usv_sim.digital_twin.process_model import ProcessParams

Array = npt.NDArray[np.float64]

# State order: [x, y, psi, v, r, b_g]
X_X, X_Y, X_PSI, X_V, X_R, X_BG = range(6)

# Default model params for scenarios (TODO: replace with tuned/identified values)
DEFAULT_PARAMS = ProcessParams(
    tau_v=1.0,
    tau_r=1.0,
    k_v=1.0,
    k_r=1.0,
)


@dataclass(frozen=True)
class Scenario:
    name: str
    dt: float
    U: Array  # shape (N, 2) = [u_s_ach, u_d_ach] achieved actuation in process-model convention
    x0: Array  # shape (6,)
    params: ProcessParams
