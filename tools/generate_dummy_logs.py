#!/usr/bin/env python
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Callable

import numpy as np


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


REPO_ROOT = _repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

USV_SIM_ROOT = REPO_ROOT / "tools" / "usv_sim"
if str(USV_SIM_ROOT) not in sys.path:
    sys.path.insert(0, str(USV_SIM_ROOT))

from analysis.sims.scenarios.circle import make_constant_turn
from analysis.sims.scenarios.step import make_step_us
from analysis.sims.scenarios.zigzag import make_zigzag_ud
from usv_sim.digital_twin.current import FW_MODEL_ID, FW_MODEL_SCHEMA
from usv_sim.digital_twin.process_model import wrap_pi
from usv_sim.digital_twin.simulate import simulate_with_inputs
from tools.log_io.layout import (
    DEFAULT_RECORD_LAYOUTS,
    ENDIAN_LITTLE,
    FILE_HEADER_STRUCT,
    MAGIC,
    RECORD_HEADER_STRUCT,
    REC_ACTUATOR_CMD,
    REC_EKF_DIAG,
    REC_ESC_OUTPUT,
    REC_GUIDANCE_REF,
    REC_MISSION_STATE,
    REC_MIXER_FEEDBACK,
    REC_NAV_SOLUTION,
    REC_SENSOR_GNSS,
    REC_SENSOR_GYRO,
    REC_SPEED_CTRL_DEBUG,
    REC_SPEED_SCHED_DEBUG,
    REC_YAW_CTRL_DEBUG,
)

NAV_STRUCT = DEFAULT_RECORD_LAYOUTS[REC_NAV_SOLUTION].payload_struct
GUIDANCE_STRUCT = DEFAULT_RECORD_LAYOUTS[REC_GUIDANCE_REF].payload_struct
ACTUATOR_STRUCT = DEFAULT_RECORD_LAYOUTS[REC_ACTUATOR_CMD].payload_struct
ESC_STRUCT = DEFAULT_RECORD_LAYOUTS[REC_ESC_OUTPUT].payload_struct
MISSION_STATE_STRUCT = DEFAULT_RECORD_LAYOUTS[REC_MISSION_STATE].payload_struct
MIXER_FEEDBACK_STRUCT = DEFAULT_RECORD_LAYOUTS[REC_MIXER_FEEDBACK].payload_struct
SPEED_SCHED_STRUCT = DEFAULT_RECORD_LAYOUTS[REC_SPEED_SCHED_DEBUG].payload_struct
SPEED_CTRL_STRUCT = DEFAULT_RECORD_LAYOUTS[REC_SPEED_CTRL_DEBUG].payload_struct
YAW_CTRL_STRUCT = DEFAULT_RECORD_LAYOUTS[REC_YAW_CTRL_DEBUG].payload_struct
EKF_DIAG_STRUCT = DEFAULT_RECORD_LAYOUTS[REC_EKF_DIAG].payload_struct
SENSOR_GNSS_STRUCT = DEFAULT_RECORD_LAYOUTS[REC_SENSOR_GNSS].payload_struct
SENSOR_GYRO_STRUCT = DEFAULT_RECORD_LAYOUTS[REC_SENSOR_GYRO].payload_struct


def _get_git_info(repo_root: Path) -> tuple[str, bool]:
    try:
        git_sha = (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=repo_root,
                text=True,
            )
            .strip()
            .lower()
        )
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=repo_root,
                text=True,
            ).strip()
        )
        return git_sha, dirty
    except Exception:
        return "unknown", False


def _build_scenario(scenario_name: str, dt: float, duration_s: float):
    builders: dict[str, Callable[[], object]] = {
        "step": lambda: make_step_us(
            dt=dt,
            T=duration_s,
            u_s0_ach=0.0,
            u_s1_ach=0.7,
            t_step=max(dt, 0.2 * duration_s),
            u_d_ach=0.0,
        ),
        "circle": lambda: make_constant_turn(
            dt=dt,
            T=duration_s,
            u_s_ach=0.65,
            u_d_ach=0.35,
        ),
        "zigzag": lambda: make_zigzag_ud(
            dt=dt,
            T=duration_s,
            u_s_ach=0.65,
            u_d_ach_amp=0.45,
            period=max(4.0 * dt, min(20.0, duration_s / 4.0)),
        ),
    }
    return builders[scenario_name]()


def _write_record(fh, t_us: int, rec_type: int, payload: bytes) -> None:
    fh.write(RECORD_HEADER_STRUCT.pack(int(t_us), int(rec_type), len(payload)))
    fh.write(payload)


def _record_catalog_json() -> dict[str, dict[str, object]]:
    return {
        str(type_id): {
            "name": layout.name,
            "fields": list(layout.fields),
        }
        for type_id, layout in sorted(DEFAULT_RECORD_LAYOUTS.items())
    }


def _write_timeseries_bin(
    out_path: Path,
    t_us: np.ndarray,
    X: np.ndarray,
    U: np.ndarray,
    fw_model_schema: int,
) -> dict[str, int]:
    counts: dict[str, int] = {
        "REC_NAV_SOLUTION": 0,
        "REC_GUIDANCE_REF": 0,
        "REC_ACTUATOR_CMD": 0,
        "REC_ESC_OUTPUT": 0,
        "REC_MISSION_STATE": 0,
        "REC_MIXER_FEEDBACK": 0,
        "REC_SPEED_SCHED_DEBUG": 0,
        "REC_SPEED_CTRL_DEBUG": 0,
        "REC_YAW_CTRL_DEBUG": 0,
        "REC_EKF_DIAG": 0,
        "REC_SENSOR_GNSS": 0,
        "REC_SENSOR_GYRO": 0,
    }

    rng = np.random.default_rng(7)

    n_steps = U.shape[0]
    dt_s = float((int(t_us[1]) - int(t_us[0])) / 1_000_000.0) if len(t_us) > 1 else 0.05

    wp0 = np.array([float(X[0, 0]), float(X[0, 1])], dtype=np.float64)
    wp1 = np.array([float(X[n_steps // 2, 0]), float(X[n_steps // 2, 1])], dtype=np.float64)
    wp2 = np.array([float(X[-1, 0]), float(X[-1, 1])], dtype=np.float64)

    v_d_state = 0.0
    i_v = 0.0
    i_psi = 0.0
    i_r = 0.0

    kp_v = 0.9
    ki_v = 0.25
    v_ff_gain = 0.6
    kp_psi = 1.8
    ki_psi = 0.1
    kp_r = 1.1
    ki_r = 0.18
    r_max = 1.2
    a_up = 0.35
    a_down = 0.50
    d_slow = 7.5
    v_wp = 0.45
    e_psi_th = 0.65
    v_psi = 0.55

    with out_path.open("wb") as fh:
        fh.write(
            FILE_HEADER_STRUCT.pack(
                MAGIC,
                int(fw_model_schema),
                ENDIAN_LITTLE,
                int(t_us[0]),
            )
        )

        for k in range(n_steps):
            tk = int(t_us[k])

            xk = X[k]
            x_next = X[k + 1]
            x_pos = float(xk[0])
            y_pos = float(xk[1])
            psi = float(xk[2])
            v_hat = float(xk[3])
            r_hat = float(xk[4])
            b_g_hat = float(xk[5])

            # Two-segment mission model so fields exist for the full chain.
            if k < (n_steps // 2):
                idx = 0
                seg_start = wp0
                seg_end = wp1
            else:
                idx = 1
                seg_start = wp1
                seg_end = wp2

            seg_dx = float(seg_end[0] - seg_start[0])
            seg_dy = float(seg_end[1] - seg_start[1])
            seg_norm = float(np.hypot(seg_dx, seg_dy))
            if seg_norm > 1e-9:
                rel_x = x_pos - float(seg_start[0])
                rel_y = y_pos - float(seg_start[1])
                e_y = float((rel_x * seg_dy - rel_y * seg_dx) / seg_norm)
            else:
                e_y = 0.0

            d_wp = float(np.hypot(float(seg_end[0]) - x_pos, float(seg_end[1]) - y_pos))

            dx = float(x_next[0] - xk[0])
            dy = float(x_next[1] - xk[1])
            psi_d = float(np.arctan2(dy, dx)) if (dx * dx + dy * dy) > 1e-12 else psi
            e_psi = float(wrap_pi(psi_d - psi))

            # Speed scheduler terms.
            u_s_ref = float(U[k, 0])
            v_seg = max(0.0, u_s_ref)
            cap_wp_active = int(d_wp < d_slow)
            cap_psi_active = int(abs(e_psi) > e_psi_th)
            v_cap = v_seg
            if cap_wp_active:
                v_cap = min(v_cap, v_wp)
            if cap_psi_active:
                v_cap = min(v_cap, v_psi)
            dv_max_up = a_up * dt_s
            dv_max_down = a_down * dt_s
            dv = float(np.clip(v_cap - v_d_state, -dv_max_down, dv_max_up))
            v_d_state = max(0.0, v_d_state + dv)
            v_d = float(v_d_state)

            # Speed controller debug.
            e_v = float(v_d - v_hat)
            i_v = float(np.clip(i_v + (ki_v * e_v * dt_s), -1.2, 1.2))
            u_s_raw = float(v_ff_gain * v_d + (kp_v * e_v) + i_v)

            # Yaw controller debug.
            i_psi = float(np.clip(i_psi + (ki_psi * e_psi * dt_s), -0.8, 0.8))
            r_d = float(np.clip((kp_psi * e_psi) + i_psi, -r_max, r_max))
            e_r = float(r_d - r_hat)
            i_r = float(np.clip(i_r + (ki_r * e_r * dt_s), -0.8, 0.8))
            u_d_raw = float((kp_r * e_r) + i_r)

            u_s_cmd = float(np.clip(u_s_raw, -1.0, 1.0))
            u_d_cmd = float(np.clip(u_d_raw, -1.0, 1.0))
            sat_u_s = int(abs(u_s_cmd - u_s_raw) > 1e-6)
            sat_u_d = int(abs(u_d_cmd - u_d_raw) > 1e-6)

            u_l_pre = float(u_s_cmd - u_d_cmd)
            u_r_pre = float(u_s_cmd + u_d_cmd)
            u_l = float(np.clip(u_l_pre, -1.0, 1.0))
            u_r = float(np.clip(u_r_pre, -1.0, 1.0))
            sat_l = int(abs(u_l - u_l_pre) > 1e-6)
            sat_r = int(abs(u_r - u_r_pre) > 1e-6)
            sat_any = int(bool(sat_l or sat_r))
            u_s_ach = float(0.5 * (u_l + u_r))
            u_d_ach = float(0.5 * (u_r - u_l))

            # EKF and sensor diagnostics are synthetic but structurally correct.
            speed_mag = float(np.hypot(dx, dy) / max(dt_s, 1e-6))
            cog = float(np.arctan2(dy, dx)) if (dx * dx + dy * dy) > 1e-12 else psi
            gnss_x = x_pos + float(rng.normal(0.0, 0.35))
            gnss_y = y_pos + float(rng.normal(0.0, 0.35))
            gnss_sog = speed_mag + float(rng.normal(0.0, 0.05))
            gnss_cog = cog + float(rng.normal(0.0, 0.03))
            gyro_z = r_hat + b_g_hat + float(rng.normal(0.0, 0.01))
            status_flags = 1 if abs(e_psi) < 1.3 else 0

            nav_payload = NAV_STRUCT.pack(
                x_pos,
                y_pos,
                psi,
                v_hat,
                r_hat,
                b_g_hat,
            )
            _write_record(fh, tk, REC_NAV_SOLUTION, nav_payload)
            counts["REC_NAV_SOLUTION"] += 1

            guidance_payload = GUIDANCE_STRUCT.pack(psi_d, v_d, e_y, e_psi)
            _write_record(fh, tk, REC_GUIDANCE_REF, guidance_payload)
            counts["REC_GUIDANCE_REF"] += 1

            mission_payload = MISSION_STATE_STRUCT.pack(
                idx,
                1 if k < (n_steps - 1) else 0,
                1 if k >= (n_steps - 1) else 0,
                float(seg_start[0]),
                float(seg_start[1]),
                float(seg_end[0]),
                float(seg_end[1]),
                v_seg,
                d_wp,
            )
            _write_record(fh, tk, REC_MISSION_STATE, mission_payload)
            counts["REC_MISSION_STATE"] += 1

            sched_payload = SPEED_SCHED_STRUCT.pack(
                v_seg,
                v_cap,
                v_d,
                e_psi,
                d_wp,
                dv,
                cap_wp_active,
                cap_psi_active,
            )
            _write_record(fh, tk, REC_SPEED_SCHED_DEBUG, sched_payload)
            counts["REC_SPEED_SCHED_DEBUG"] += 1

            speed_ctrl_payload = SPEED_CTRL_STRUCT.pack(
                v_d,
                v_hat,
                e_v,
                u_s_raw,
                u_s_cmd,
                i_v,
                sat_u_s,
            )
            _write_record(fh, tk, REC_SPEED_CTRL_DEBUG, speed_ctrl_payload)
            counts["REC_SPEED_CTRL_DEBUG"] += 1

            yaw_ctrl_payload = YAW_CTRL_STRUCT.pack(
                psi_d,
                psi,
                e_psi,
                r_d,
                r_hat,
                e_r,
                u_d_cmd,
                sat_u_d,
            )
            _write_record(fh, tk, REC_YAW_CTRL_DEBUG, yaw_ctrl_payload)
            counts["REC_YAW_CTRL_DEBUG"] += 1

            actuator_payload = ACTUATOR_STRUCT.pack(u_s_cmd, u_d_cmd)
            _write_record(fh, tk, REC_ACTUATOR_CMD, actuator_payload)
            counts["REC_ACTUATOR_CMD"] += 1

            mix_payload = MIXER_FEEDBACK_STRUCT.pack(
                u_s_ach,
                u_d_ach,
                sat_l,
                sat_r,
                sat_any,
                u_l,
                u_r,
            )
            _write_record(fh, tk, REC_MIXER_FEEDBACK, mix_payload)
            counts["REC_MIXER_FEEDBACK"] += 1

            esc_payload = ESC_STRUCT.pack(u_l, u_r)
            _write_record(fh, tk, REC_ESC_OUTPUT, esc_payload)
            counts["REC_ESC_OUTPUT"] += 1

            ekf_diag_payload = EKF_DIAG_STRUCT.pack(
                0.20 + (0.05 * abs(e_psi)),
                0.20 + (0.05 * abs(e_psi)),
                0.08 + (0.03 * abs(r_hat)),
                0.15 + (0.04 * abs(e_v)),
                0.12 + (0.04 * abs(e_r)),
                0.02 + (0.01 * abs(b_g_hat)),
                int(status_flags),
            )
            _write_record(fh, tk, REC_EKF_DIAG, ekf_diag_payload)
            counts["REC_EKF_DIAG"] += 1

            gnss_payload = SENSOR_GNSS_STRUCT.pack(
                gnss_x,
                gnss_y,
                gnss_cog,
                gnss_sog,
                1,
            )
            _write_record(fh, tk, REC_SENSOR_GNSS, gnss_payload)
            counts["REC_SENSOR_GNSS"] += 1

            gyro_payload = SENSOR_GYRO_STRUCT.pack(
                gyro_z,
                b_g_hat,
                1,
            )
            _write_record(fh, tk, REC_SENSOR_GYRO, gyro_payload)
            counts["REC_SENSOR_GYRO"] += 1

        x_final = X[-1]
        _write_record(
            fh,
            int(t_us[-1]),
            REC_NAV_SOLUTION,
            NAV_STRUCT.pack(
                float(x_final[0]),
                float(x_final[1]),
                float(x_final[2]),
                float(x_final[3]),
                float(x_final[4]),
                float(x_final[5]),
            ),
        )
        counts["REC_NAV_SOLUTION"] += 1

    return counts


def _write_events_jsonl(
    out_path: Path,
    t_us: np.ndarray,
    scenario_name: str,
    git_sha: str,
    git_dirty: bool,
    fw_model_schema: int,
) -> int:
    dt_us = int(t_us[1] - t_us[0]) if len(t_us) > 1 else 0
    t0 = int(t_us[0])
    tm = int(t_us[len(t_us) // 2])
    t_end = int(t_us[-1])

    events = [
        {
            "t_us": t0,
            "type": "FW_INFO",
            "git_sha": git_sha,
            "git_dirty": git_dirty,
            "fw_model_schema": int(fw_model_schema),
        },
        {
            "t_us": t0 + dt_us,
            "type": "MODE_CHANGE",
            "from": "MANUAL",
            "to": "AUTOPILOT",
            "reason": "DUMMY_LOG_GENERATOR",
        },
        {
            "t_us": t0 + (2 * dt_us),
            "type": "MISSION_START",
            "scenario": scenario_name,
        },
        {
            "t_us": t0 + (3 * dt_us),
            "type": "PARAM_APPLY",
            "id": "control.kp_speed",
            "old": 0.7,
            "new": 0.8,
        },
        {
            "t_us": tm,
            "type": "EKF_GATING",
            "sensor": "GNSS",
            "metric": "NIS_POS",
            "action": "ACCEPT",
        },
        {
            "t_us": tm + dt_us,
            "type": "WP_SWITCH",
            "idx": 1,
            "d_wp": 5.0,
        },
        {
            "t_us": t_end,
            "type": "MISSION_DONE",
            "reason": "END_OF_SCENARIO",
        },
    ]

    with out_path.open("w", encoding="utf-8", newline="\n") as fh:
        for event in events:
            fh.write(json.dumps(event, separators=(",", ":")) + "\n")

    return len(events)


def generate_dummy_log_session(
    output_root: Path,
    scenario_name: str,
    duration_s: float,
    dt: float,
    session_name: str | None = None,
) -> Path:
    if dt <= 0.0:
        raise ValueError("dt must be > 0")
    if duration_s <= 0.0:
        raise ValueError("duration_s must be > 0")

    if session_name is None:
        session_name = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    session_dir = output_root / session_name
    session_dir.mkdir(parents=True, exist_ok=False)

    scenario = _build_scenario(scenario_name, dt, duration_s)
    t_s, X, U = simulate_with_inputs(
        x0=scenario.x0,
        U_in=scenario.U,
        dt=scenario.dt,
        params=scenario.params,
        dtype=np.float64,
    )
    t_us = np.round(t_s * 1_000_000.0).astype(np.uint64)

    git_sha, git_dirty = _get_git_info(REPO_ROOT)

    timeseries_path = session_dir / "timeseries.bin"
    record_counts = _write_timeseries_bin(
        out_path=timeseries_path,
        t_us=t_us,
        X=X,
        U=U,
        fw_model_schema=FW_MODEL_SCHEMA,
    )

    events_path = session_dir / "events.jsonl"
    event_count = _write_events_jsonl(
        out_path=events_path,
        t_us=t_us,
        scenario_name=scenario.name,
        git_sha=git_sha,
        git_dirty=git_dirty,
        fw_model_schema=FW_MODEL_SCHEMA,
    )

    created_utc = datetime.now(timezone.utc).isoformat()
    meta = {
        "created_utc": created_utc,
        "session_name": session_name,
        "generator": "tools/generate_dummy_logs.py",
        "git_sha": git_sha,
        "git_dirty": git_dirty,
        "fw_model_id": FW_MODEL_ID,
        "fw_model_schema": int(FW_MODEL_SCHEMA),
        "scenario": {
            "name": scenario.name,
            "dt_s": float(scenario.dt),
            "duration_s": float(duration_s),
            "n_steps": int(U.shape[0]),
        },
        "process_params": asdict(scenario.params),
        "time": {
            "t0_us": int(t_us[0]),
            "t_end_us": int(t_us[-1]),
            "dt_us": int(t_us[1] - t_us[0]) if len(t_us) > 1 else 0,
        },
        "params_snapshot": {
            "guidance.lookahead_m": 8.0,
            "control.kp_heading": 1.2,
            "control.kp_speed": 0.8,
        },
        "files": {
            "timeseries.bin": {
                "format": "tlv_v1",
                "header": {
                    "magic": MAGIC.decode("ascii"),
                    "endianness": "little",
                    "fw_model_schema": int(FW_MODEL_SCHEMA),
                },
                "record_catalog": _record_catalog_json(),
                "record_counts": record_counts,
            },
            "events.jsonl": {
                "event_count": event_count,
            },
        },
    }

    meta_path = session_dir / "meta.json"
    with meta_path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, indent=2)
        fh.write("\n")

    return session_dir


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a dummy STM32-style log session folder for local testing."
    )
    parser.add_argument(
        "--scenario",
        choices=("step", "circle", "zigzag"),
        default="step",
        help="Scenario profile to synthesize.",
    )
    parser.add_argument(
        "--duration-s",
        type=float,
        default=60.0,
        help="Scenario duration in seconds.",
    )
    parser.add_argument(
        "--dt",
        type=float,
        default=0.05,
        help="Sample period in seconds.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("logs"),
        help="Directory that will contain session subfolders.",
    )
    parser.add_argument(
        "--session-name",
        type=str,
        default=None,
        help="Optional explicit session folder name (default YYYYMMDD_HHMMSS UTC).",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    session_dir = generate_dummy_log_session(
        output_root=args.output_root,
        scenario_name=args.scenario,
        duration_s=args.duration_s,
        dt=args.dt,
        session_name=args.session_name,
    )
    print(f"Created dummy log session: {session_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
