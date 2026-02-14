#!/usr/bin/env python3
"""Minimal docs consistency check for actuation naming.

Intentionally small for solo-dev maintenance:
- catch stage-name drift (req/cmd/alloc/ach)
- catch missing core topics (ACTUATOR_REQ/ACTUATOR_CMD/MIXER_FEEDBACK)
- only scan a few docs that define contract + dataflow + backend behavior
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    Path("docs/interfaces/contracts.md"),
    Path("docs/interfaces/dataflow.md"),
    Path("docs/control/mixer_and_limits.md"),
]

GLOBAL_TOKENS = [
    "ACTUATOR_REQ",
    "ACTUATOR_CMD",
    "MIXER_FEEDBACK",
    "u_s_req",
    "u_s_cmd",
    "u_s^{alloc}",
    "u_s_ach",
    "u_d_req",
    "u_d_cmd",
    "u_d^{alloc}",
    "u_d_ach",
]

PER_FILE_TOKENS = {
    "docs/interfaces/contracts.md": ["actuator_req_t", "actuator_cmd_t", "mixer_feedback_t"],
    "docs/interfaces/dataflow.md": ["publish:", "consume:", "MIXER_FEEDBACK"],
    "docs/control/mixer_and_limits.md": ["u_s^{alloc}", "u_d^{alloc}", "u_s^{ach}", "u_d^{ach}"],
}


def main() -> int:
    errors: list[str] = []
    texts: dict[str, str] = {}

    for rel in DOCS:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing file: {rel.as_posix()}")
            continue
        texts[rel.as_posix()] = path.read_text(encoding="utf-8")

    corpus = "\n".join(texts.values())

    for token in GLOBAL_TOKENS:
        if token not in corpus:
            errors.append(f"missing global token: {token}")

    for rel, tokens in PER_FILE_TOKENS.items():
        text = texts.get(rel, "")
        for token in tokens:
            if token not in text:
                errors.append(f"missing in {rel}: {token}")

    if errors:
        print("Docs consistency check failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Docs consistency check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
