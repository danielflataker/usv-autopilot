from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.generate_dummy_logs import generate_dummy_log_session
from tools.log_io import iter_mavlink_telemetry, read_timeseries_bin


class DummyTelemetryTests(unittest.TestCase):
    def test_iter_mavlink_telemetry_emits_predefined_messages(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_root = Path(td) / "logs"
            session = generate_dummy_log_session(
                output_root=out_root,
                scenario_name="step",
                duration_s=2.0,
                dt=0.1,
                session_name="tm_session",
            )
            timeseries = read_timeseries_bin(session / "timeseries.bin")
            msgs = list(
                iter_mavlink_telemetry(
                    timeseries,
                    events_jsonl=session / "events.jsonl",
                    heartbeat_hz=1.0,
                    status_hz=1.0,
                    pose_hz=5.0,
                    include_custom_messages=False,
                )
            )

        names = {m.name for m in msgs}
        self.assertIn("HEARTBEAT", names)
        self.assertIn("SYS_STATUS", names)
        self.assertIn("LOCAL_POSITION_NED", names)
        self.assertIn("ATTITUDE", names)
        self.assertIn("STATUSTEXT", names)
        self.assertIn("PARAM_EXT_ACK", names)


if __name__ == "__main__":
    unittest.main()

