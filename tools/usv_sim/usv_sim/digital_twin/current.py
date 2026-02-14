# tools/usv_sim/usv_sim/digital_twin/current.py
from __future__ import annotations

from .process_model import ProcessParams, process_step
from .simulate import simulate, simulate_with_inputs
from .estimation import ExtendedKalmanFilter

FW_MODEL_ID = "proc_model_2d_surgev_yawrate_bias"
FW_MODEL_SCHEMA = 1  # keep naming consistent with firmware/docs

__all__ = [
    "FW_MODEL_ID",
    "FW_MODEL_SCHEMA",
    "ProcessParams",
    "process_step",
    "simulate",
    "simulate_with_inputs",
    "ExtendedKalmanFilter",
]
