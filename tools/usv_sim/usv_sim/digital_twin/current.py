# tools/usv_sim/usv_sim/digital_twin/current.py
from __future__ import annotations

from .process_model import ProcessParams, process_step
from .simulate import simulate, simulate_with_inputs

FW_MODEL_ID = "proc_model_2d_surgev_yawrate_bias"
FW_MODEL_SCHEMA = 1  # keep naming consistent with firmware/docs
