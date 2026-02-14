from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.log_io.layout import DEFAULT_RECORD_LAYOUTS


class LoggingContractSyncTests(unittest.TestCase):
    def test_layout_ids_and_payload_sizes_are_sane(self) -> None:
        ids = list(DEFAULT_RECORD_LAYOUTS.keys())
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(type_id > 0 for type_id in ids))
        for layout in DEFAULT_RECORD_LAYOUTS.values():
            # `len` field in TLV header is uint16.
            self.assertLessEqual(layout.payload_struct.size, 0xFFFF)

    def test_firmware_record_enum_sync_placeholder(self) -> None:
        record_header = REPO_ROOT / "firmware" / "src" / "logging" / "record_types.h"
        if not record_header.exists():
            self.skipTest(
                f"Firmware record enum header not found yet: {record_header}. "
                "Enable this test when firmware logging headers are added."
            )

        text = record_header.read_text(encoding="utf-8")
        c_defs = {
            name: int(val)
            for name, val in re.findall(r"#define\s+(REC_[A-Z0-9_]+)\s+(\d+)", text)
        }
        py_defs = {layout.name: layout.type_id for layout in DEFAULT_RECORD_LAYOUTS.values()}
        self.assertEqual(c_defs, py_defs)


if __name__ == "__main__":
    unittest.main()
