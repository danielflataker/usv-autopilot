from __future__ import annotations

from dataclasses import dataclass
import struct
from typing import Final


MAGIC: Final[bytes] = b"USVLOG"
ENDIAN_LITTLE: Final[int] = 1

# 32-byte fixed header:
# magic[6], fw_model_schema[uint32], endianness[uint8], t0_us[uint64], reserved[13]
FILE_HEADER_STRUCT: Final[struct.Struct] = struct.Struct("<6sIBQ13x")
# Per-record header: t_us[uint64], type[uint16], len[uint16]
RECORD_HEADER_STRUCT: Final[struct.Struct] = struct.Struct("<QHH")


REC_NAV_SOLUTION: Final[int] = 1
REC_GUIDANCE_REF: Final[int] = 2
REC_ACTUATOR_REQ: Final[int] = 3
REC_ACTUATOR_CMD: Final[int] = 4
REC_ESC_OUTPUT: Final[int] = 5
REC_MISSION_STATE: Final[int] = 6
REC_MIXER_FEEDBACK: Final[int] = 7
REC_SPEED_SCHED_DEBUG: Final[int] = 8
REC_SPEED_CTRL_DEBUG: Final[int] = 9
REC_YAW_CTRL_DEBUG: Final[int] = 10
REC_EKF_DIAG: Final[int] = 11
REC_SENSOR_GNSS: Final[int] = 12
REC_SENSOR_GYRO: Final[int] = 13


@dataclass(frozen=True, slots=True)
class RecordLayout:
    type_id: int
    name: str
    fields: tuple[str, ...]
    payload_struct: struct.Struct


DEFAULT_RECORD_LAYOUTS: Final[dict[int, RecordLayout]] = {
    REC_NAV_SOLUTION: RecordLayout(
        type_id=REC_NAV_SOLUTION,
        name="REC_NAV_SOLUTION",
        fields=("x", "y", "psi", "v", "r", "b_g"),
        payload_struct=struct.Struct("<6f"),
    ),
    REC_GUIDANCE_REF: RecordLayout(
        type_id=REC_GUIDANCE_REF,
        name="REC_GUIDANCE_REF",
        fields=("psi_d", "v_d", "e_y", "e_psi"),
        payload_struct=struct.Struct("<4f"),
    ),
    REC_ACTUATOR_REQ: RecordLayout(
        type_id=REC_ACTUATOR_REQ,
        name="REC_ACTUATOR_REQ",
        fields=("u_s_req", "u_d_req", "src"),
        payload_struct=struct.Struct("<2fB3x"),
    ),
    REC_ACTUATOR_CMD: RecordLayout(
        type_id=REC_ACTUATOR_CMD,
        name="REC_ACTUATOR_CMD",
        fields=("u_s_cmd", "u_d_cmd"),
        payload_struct=struct.Struct("<2f"),
    ),
    REC_ESC_OUTPUT: RecordLayout(
        type_id=REC_ESC_OUTPUT,
        name="REC_ESC_OUTPUT",
        fields=("u_L", "u_R"),
        payload_struct=struct.Struct("<2f"),
    ),
    REC_MISSION_STATE: RecordLayout(
        type_id=REC_MISSION_STATE,
        name="REC_MISSION_STATE",
        fields=("idx", "active", "done", "x0", "y0", "x1", "y1", "v_seg", "d_wp"),
        payload_struct=struct.Struct("<HBB4x6f"),
    ),
    REC_MIXER_FEEDBACK: RecordLayout(
        type_id=REC_MIXER_FEEDBACK,
        name="REC_MIXER_FEEDBACK",
        fields=("u_s_ach", "u_d_ach", "sat_L", "sat_R", "sat_any", "u_L_ach", "u_R_ach"),
        payload_struct=struct.Struct("<2f3B5x2f"),
    ),
    REC_SPEED_SCHED_DEBUG: RecordLayout(
        type_id=REC_SPEED_SCHED_DEBUG,
        name="REC_SPEED_SCHED_DEBUG",
        fields=("v_seg", "v_cap", "v_d", "e_psi", "d_wp", "dv", "cap_wp", "cap_psi"),
        payload_struct=struct.Struct("<6f2B2x"),
    ),
    REC_SPEED_CTRL_DEBUG: RecordLayout(
        type_id=REC_SPEED_CTRL_DEBUG,
        name="REC_SPEED_CTRL_DEBUG",
        fields=("v_d", "v_hat", "e_v", "u_s_raw", "u_s_req", "i_v", "sat_u_s"),
        payload_struct=struct.Struct("<6fB3x"),
    ),
    REC_YAW_CTRL_DEBUG: RecordLayout(
        type_id=REC_YAW_CTRL_DEBUG,
        name="REC_YAW_CTRL_DEBUG",
        fields=("psi_d", "psi", "e_psi", "r_d", "r", "e_r", "u_d_req", "sat_u_d"),
        payload_struct=struct.Struct("<7fB3x"),
    ),
    REC_EKF_DIAG: RecordLayout(
        type_id=REC_EKF_DIAG,
        name="REC_EKF_DIAG",
        fields=("P_xx", "P_yy", "P_psi", "P_v", "P_r", "P_bg", "status_flags"),
        payload_struct=struct.Struct("<6fI"),
    ),
    REC_SENSOR_GNSS: RecordLayout(
        type_id=REC_SENSOR_GNSS,
        name="REC_SENSOR_GNSS",
        fields=("x", "y", "cog", "sog", "valid"),
        payload_struct=struct.Struct("<4fB3x"),
    ),
    REC_SENSOR_GYRO: RecordLayout(
        type_id=REC_SENSOR_GYRO,
        name="REC_SENSOR_GYRO",
        fields=("z_gyro", "b_g_est", "valid"),
        payload_struct=struct.Struct("<2fB3x"),
    ),
}

