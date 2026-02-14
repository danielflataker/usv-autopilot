"""
Digital twin models.

Goal: match the currently deployed firmware model (contracts, units, schema).
Use this package from analysis/tools when you want "same as firmware".
"""

from .contracts import INPUT_DIM, STATE_DIM
from .current import FW_MODEL_ID, FW_MODEL_SCHEMA
from .estimation import ExtendedKalmanFilter, EkfState
from .process_model import ProcessParams, process_step, wrap_pi
from .simulate import simulate, simulate_with_inputs

__all__ = [
    "FW_MODEL_ID",
    "FW_MODEL_SCHEMA",
    "STATE_DIM",
    "INPUT_DIM",
    "ProcessParams",
    "process_step",
    "wrap_pi",
    "simulate",
    "simulate_with_inputs",
    "EkfState",
    "ExtendedKalmanFilter",
]
