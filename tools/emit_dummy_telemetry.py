#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.log_io import iter_mavlink_telemetry, read_timeseries_bin


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit dummy MAVLink-aligned telemetry messages from a log session."
    )
    parser.add_argument(
        "--session-dir",
        type=Path,
        required=True,
        help="Session folder containing timeseries.bin and events.jsonl.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional output JSONL file (default: stdout).",
    )
    parser.add_argument("--heartbeat-hz", type=float, default=1.0)
    parser.add_argument("--status-hz", type=float, default=1.0)
    parser.add_argument("--pose-hz", type=float, default=5.0)
    parser.add_argument(
        "--include-custom",
        action="store_true",
        help="Also emit custom (non-predefined) USV debug/event messages.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    timeseries_path = args.session_dir / "timeseries.bin"
    events_path = args.session_dir / "events.jsonl"

    data = read_timeseries_bin(timeseries_path)
    msgs = iter_mavlink_telemetry(
        data,
        events_jsonl=events_path,
        heartbeat_hz=args.heartbeat_hz,
        status_hz=args.status_hz,
        pose_hz=args.pose_hz,
        include_custom_messages=args.include_custom,
    )

    if args.out is None:
        for msg in msgs:
            print(
                json.dumps(
                    {
                        "t_us": msg.t_us,
                        "name": msg.name,
                        "predefined": msg.predefined,
                        "payload": msg.payload,
                    },
                    separators=(",", ":"),
                )
            )
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", encoding="utf-8", newline="\n") as fh:
            for msg in msgs:
                fh.write(
                    json.dumps(
                        {
                            "t_us": msg.t_us,
                            "name": msg.name,
                            "predefined": msg.predefined,
                            "payload": msg.payload,
                        },
                        separators=(",", ":"),
                    )
                    + "\n"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
