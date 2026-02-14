from __future__ import annotations

import json
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
from usv_sim.digital_twin.current import FW_MODEL_SCHEMA
from tools.log_io import FILE_HEADER_STRUCT, RECORD_HEADER_STRUCT, read_timeseries_bin
from tools.log_io.layout import MAGIC, REC_NAV_SOLUTION


class TimeseriesIoTests(unittest.TestCase):
    def test_read_timeseries_bin_decodes_dummy_session(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_root = Path(td) / "logs"
            session = generate_dummy_log_session(
                output_root=out_root,
                scenario_name="step",
                duration_s=2.0,
                dt=0.1,
                session_name="test_session",
            )
            parsed = read_timeseries_bin(session / "timeseries.bin")
            meta = json.loads((session / "meta.json").read_text(encoding="utf-8"))

        n_steps = int(meta["scenario"]["n_steps"])
        self.assertEqual(parsed.header.magic, "USVLOG")
        self.assertEqual(parsed.header.fw_model_schema, FW_MODEL_SCHEMA)
        self.assertEqual(parsed.record_counts["REC_NAV_SOLUTION"], n_steps + 1)
        self.assertEqual(parsed.record_counts["REC_GUIDANCE_REF"], n_steps)
        self.assertEqual(parsed.record_counts["REC_MIXER_FEEDBACK"], n_steps)

        nav = parsed.records["REC_NAV_SOLUTION"]
        self.assertEqual(nav["x"].shape[0], n_steps + 1)
        self.assertEqual(nav["t_us"].dtype.kind, "u")
        self.assertEqual(len(parsed.unknown_records), 0)

    def test_unknown_record_is_skipped_and_reported(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "timeseries.bin"
            with p.open("wb") as fh:
                fh.write(FILE_HEADER_STRUCT.pack(MAGIC, 1, 1, 0))
                fh.write(RECORD_HEADER_STRUCT.pack(10, 999, 4))
                fh.write(b"ABCD")

            parsed = read_timeseries_bin(p, keep_unknown=True)

        self.assertEqual(len(parsed.unknown_records), 1)
        self.assertEqual(parsed.unknown_records[0].type_id, 999)
        self.assertEqual(parsed.record_counts, {})

    def test_payload_length_mismatch_raises_in_strict_mode(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "timeseries.bin"
            with p.open("wb") as fh:
                fh.write(FILE_HEADER_STRUCT.pack(MAGIC, 1, 1, 0))
                fh.write(RECORD_HEADER_STRUCT.pack(5, REC_NAV_SOLUTION, 3))
                fh.write(b"\x00\x00\x00")

            with self.assertRaisesRegex(ValueError, "payload length mismatch"):
                read_timeseries_bin(p)


if __name__ == "__main__":
    unittest.main()
