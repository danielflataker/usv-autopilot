#!/usr/bin/env python3
"""Lightweight docs consistency check for actuation-pipeline naming.

This script guards against naming drift across core docs by validating:
- required pipeline topics: ACTUATOR_REQ, ACTUATOR_CMD, MIXER_FEEDBACK
- required stage naming terms: req/cmd/alloc/ach in both math and field style
- per-file anchor terms for key contracts/dataflow/pipeline docs
- obvious encoding artifacts (replacement character)
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

CORE_DOCS = [
    Path("docs/control/actuation_command_pipeline_spec.md"),
    Path("docs/control/command_shaping.md"),
    Path("docs/control/mixer_and_limits.md"),
    Path("docs/interfaces/contracts.md"),
    Path("docs/interfaces/dataflow.md"),
    Path("docs/logging/record_formats.md"),
]

GLOBAL_REQUIRED = [
    "ACTUATOR_REQ",
    "ACTUATOR_CMD",
    "MIXER_FEEDBACK",
    "u_s_req",
    "u_d_req",
    "u_s_cmd",
    "u_d_cmd",
    "u_s_ach",
    "u_d_ach",
]

GLOBAL_REGEX = {
    "math req": r"u_\*\^\{req\}|u_s\^\{req\}",
    "math cmd": r"u_\*\^\{cmd\}|u_s\^\{cmd\}",
    "math alloc": r"u_\*\^\{alloc\}|u_s\^\{alloc\}",
    "math ach": r"u_\*\^\{ach\}|u_s\^\{ach\}",
}

PER_FILE_REQUIRED = {
    "docs/interfaces/contracts.md": [
        "ACTUATOR_REQ",
        "ACTUATOR_CMD",
        "MIXER_FEEDBACK",
        "actuator_req_t",
        "actuator_cmd_t",
        "mixer_feedback_t",
    ],
    "docs/interfaces/dataflow.md": [
        "ACTUATOR_REQ",
        "ACTUATOR_CMD",
        "MIXER_FEEDBACK",
        "publish:",
        "consume:",
    ],
    "docs/control/actuation_command_pipeline_spec.md": [
        "Stage 0",
        "Stage 1",
        "Stage 2",
        "Stage 3",
        "u_s^{req}",
        "u_s^{cmd}",
        "u_s^{alloc}",
        "u_s^{ach}",
    ],
    "docs/control/command_shaping.md": [
        "u_s_req",
        "u_s_cmd",
        "act.shp.ap.u_s_scale",
        "act.shp.man.u_d_scale",
    ],
    "docs/control/mixer_and_limits.md": [
        "u_s^{alloc}",
        "u_d^{alloc}",
        "u_s^{ach}",
        "u_d^{ach}",
        "u_d_max_pos",
        "u_d_max_neg",
    ],
}

ENCODING_RED_FLAGS = ["�"]


def main() -> int:
    errors: list[str] = []
    texts: dict[str, str] = {}

    for rel in CORE_DOCS:
        p = ROOT / rel
        if not p.exists():
            errors.append(f"Missing required doc file: {rel}")
            continue
        texts[str(rel)] = p.read_text(encoding="utf-8")

    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1

    corpus = "\n".join(texts.values())

    for token in GLOBAL_REQUIRED:
        if token not in corpus:
            errors.append(f"Missing global token: {token}")

    for name, pattern in GLOBAL_REGEX.items():
        if not re.search(pattern, corpus):
            errors.append(f"Missing global stage regex ({name}): /{pattern}/")

    for rel, reqs in PER_FILE_REQUIRED.items():
        text = texts.get(rel, "")
        for token in reqs:
            if token not in text:
                errors.append(f"Missing in {rel}: {token}")

    for rel, text in texts.items():
        for bad in ENCODING_RED_FLAGS:
            if bad in text:
                errors.append(f"Encoding artifact in {rel}: contains '{bad}'")

    if errors:
        print("Docs consistency check failed:\n")
        for e in errors:
            print(f"- {e}")
        return 1

    print("Docs consistency check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
