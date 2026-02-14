from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterator

import numpy as np

from .io import TimeseriesData

# Messages we can map directly onto MAVLink common set.
PREDEFINED_MAVLINK_MESSAGES: dict[str, str] = {
    "heartbeat": "HEARTBEAT",
    "status": "SYS_STATUS",
    "ekf_status": "ESTIMATOR_STATUS",
    "pose_local": "LOCAL_POSITION_NED",
    "pose_attitude": "ATTITUDE",
    "event_text": "STATUSTEXT",
    "param_ack": "PARAM_EXT_ACK",
}

# Messages that should stay custom if we want rich USV-specific debug payloads.
CUSTOM_MAVLINK_MESSAGES: dict[str, str] = {
    "event_structured": "USV_EVENT",
    "ctrl_debug": "USV_CTRL_DEBUG",
    "mixer_feedback": "USV_MIXER_FEEDBACK",
}


@dataclass(frozen=True, slots=True)
class TelemetryMessage:
    t_us: int
    name: str
    payload: dict[str, Any]
    predefined: bool


def _read_events_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def _severity_for_event(event_type: str) -> int:
    if event_type in {"LOG_OVERFLOW", "LINK_LOSS"}:
        return 4  # warning
    if event_type in {"EKF_GATING"}:
        return 6  # info
    return 6  # info by default


def iter_mavlink_telemetry(
    timeseries: TimeseriesData,
    *,
    events_jsonl: Path | None = None,
    heartbeat_hz: float = 1.0,
    status_hz: float = 1.0,
    pose_hz: float = 5.0,
    include_custom_messages: bool = False,
) -> Iterator[TelemetryMessage]:
    """Yield MAVLink-aligned telemetry messages from parsed timeseries data.

    This emits message payload dictionaries (not binary MAVLink frames) so the same
    mapping can be reused by dummy and real transports.
    """
    if heartbeat_hz <= 0.0 or status_hz <= 0.0 or pose_hz <= 0.0:
        raise ValueError("heartbeat_hz, status_hz, and pose_hz must all be > 0")

    nav = timeseries.records.get("REC_NAV_SOLUTION")
    if nav is None:
        raise ValueError("timeseries is missing REC_NAV_SOLUTION; cannot emit telemetry")

    ekf = timeseries.records.get("REC_EKF_DIAG")
    speed_ctrl = timeseries.records.get("REC_SPEED_CTRL_DEBUG")
    yaw_ctrl = timeseries.records.get("REC_YAW_CTRL_DEBUG")
    mixer = timeseries.records.get("REC_MIXER_FEEDBACK")

    t_nav = nav["t_us"].astype(np.uint64)
    next_hb = int(t_nav[0])
    next_status = int(t_nav[0])
    next_pose = int(t_nav[0])

    hb_dt_us = int(round(1_000_000.0 / heartbeat_hz))
    status_dt_us = int(round(1_000_000.0 / status_hz))
    pose_dt_us = int(round(1_000_000.0 / pose_hz))

    t_start = int(t_nav[0])
    t_end = int(t_nav[-1]) if len(t_nav) > 1 else t_start
    span = max(1, t_end - t_start)

    for i, t_u64 in enumerate(t_nav):
        t_us = int(t_u64)

        if t_us >= next_hb:
            yield TelemetryMessage(
                t_us=t_us,
                name=PREDEFINED_MAVLINK_MESSAGES["heartbeat"],
                predefined=True,
                payload={
                    "type": 11,  # MAV_TYPE_SURFACE_BOAT
                    "autopilot": 12,  # MAV_AUTOPILOT_GENERIC
                    "base_mode": 0,
                    "custom_mode": 0,
                    "system_status": 4,  # MAV_STATE_ACTIVE
                    "mavlink_version": 3,
                },
            )
            next_hb += hb_dt_us

        if t_us >= next_status:
            frac = float(t_us - t_start) / float(span)
            battery_remaining = int(max(0.0, 100.0 - 8.0 * frac))
            voltage_mv = int(16800 - (400 * frac))
            yield TelemetryMessage(
                t_us=t_us,
                name=PREDEFINED_MAVLINK_MESSAGES["status"],
                predefined=True,
                payload={
                    "onboard_control_sensors_present": 0,
                    "onboard_control_sensors_enabled": 0,
                    "onboard_control_sensors_health": 0,
                    "voltage_battery": voltage_mv,
                    "current_battery": -1,
                    "battery_remaining": battery_remaining,
                },
            )

            if ekf is not None and i < len(ekf["t_us"]):
                flags = int(ekf["status_flags"][i])
                yield TelemetryMessage(
                    t_us=t_us,
                    name=PREDEFINED_MAVLINK_MESSAGES["ekf_status"],
                    predefined=True,
                    payload={
                        "flags": flags,
                        "vel_variance": float(ekf["P_v"][i]),
                        "pos_horiz_variance": float(ekf["P_xx"][i] + ekf["P_yy"][i]),
                        "pos_vert_variance": 0.0,
                        "compass_variance": 0.0,
                        "terrain_alt_variance": 0.0,
                    },
                )
            next_status += status_dt_us

        if t_us >= next_pose:
            psi = float(nav["psi"][i])
            v = float(nav["v"][i])
            r = float(nav["r"][i])
            yield TelemetryMessage(
                t_us=t_us,
                name=PREDEFINED_MAVLINK_MESSAGES["pose_local"],
                predefined=True,
                payload={
                    "time_boot_ms": int(t_us // 1000),
                    "x": float(nav["x"][i]),
                    "y": float(nav["y"][i]),
                    "z": 0.0,
                    "vx": float(v * np.cos(psi)),
                    "vy": float(v * np.sin(psi)),
                    "vz": 0.0,
                },
            )
            yield TelemetryMessage(
                t_us=t_us,
                name=PREDEFINED_MAVLINK_MESSAGES["pose_attitude"],
                predefined=True,
                payload={
                    "time_boot_ms": int(t_us // 1000),
                    "roll": 0.0,
                    "pitch": 0.0,
                    "yaw": psi,
                    "rollspeed": 0.0,
                    "pitchspeed": 0.0,
                    "yawspeed": r,
                },
            )

            if include_custom_messages and speed_ctrl is not None and yaw_ctrl is not None and mixer is not None:
                if i < len(speed_ctrl["t_us"]) and i < len(yaw_ctrl["t_us"]) and i < len(mixer["t_us"]):
                    yield TelemetryMessage(
                        t_us=t_us,
                        name=CUSTOM_MAVLINK_MESSAGES["ctrl_debug"],
                        predefined=False,
                        payload={
                            "v_d": float(speed_ctrl["v_d"][i]),
                            "v_hat": float(speed_ctrl["v_hat"][i]),
                            "u_s_cmd": float(speed_ctrl["u_s_cmd"][i]),
                            "u_d_cmd": float(yaw_ctrl["u_d_cmd"][i]),
                            "e_psi": float(yaw_ctrl["e_psi"][i]),
                        },
                    )
                    yield TelemetryMessage(
                        t_us=t_us,
                        name=CUSTOM_MAVLINK_MESSAGES["mixer_feedback"],
                        predefined=False,
                        payload={
                            "u_s_ach": float(mixer["u_s_ach"][i]),
                            "u_d_ach": float(mixer["u_d_ach"][i]),
                            "sat_any": int(mixer["sat_any"][i]),
                        },
                    )

            next_pose += pose_dt_us

    events = _read_events_jsonl(events_jsonl) if events_jsonl is not None else []
    for event in events:
        t_us = int(event.get("t_us", t_end))
        event_type = str(event.get("type", "EVENT"))
        txt = f"{event_type}: {json.dumps(event, separators=(',', ':'))}"
        yield TelemetryMessage(
            t_us=t_us,
            name=PREDEFINED_MAVLINK_MESSAGES["event_text"],
            predefined=True,
            payload={
                "severity": _severity_for_event(event_type),
                "text": txt[:50],  # MAVLink STATUSTEXT text length.
            },
        )

        if include_custom_messages:
            yield TelemetryMessage(
                t_us=t_us,
                name=CUSTOM_MAVLINK_MESSAGES["event_structured"],
                predefined=False,
                payload=event,
            )

        if event_type == "PARAM_APPLY":
            param_id = str(event.get("id", "unknown"))[:16]
            yield TelemetryMessage(
                t_us=t_us,
                name=PREDEFINED_MAVLINK_MESSAGES["param_ack"],
                predefined=True,
                payload={
                    "param_id": param_id,
                    "param_value": str(event.get("new", ""))[:128],
                    "param_type": 9,  # MAV_PARAM_EXT_TYPE_REAL32
                    "param_result": 0,  # MAV_PARAM_EXT_ACK_ACCEPTED
                },
            )

