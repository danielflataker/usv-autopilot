# tests/

Purpose: define testing intent and structure early, without forcing full test implementation now.

## Why this folder exists

- Keep test strategy visible at repo root.
- Avoid scattering future tests without conventions.
- Separate "test architecture" decisions from day-to-day feature work.

## Current state

- No root-level automated test suite is required yet.
- Existing Python package tests live in `tools/usv_sim/tests`.
- A docs consistency gate exists in `tools/check_docs_contracts.py`.

## Testing intent (phased)

1. Phase 0 (now): document approach, keep modules testable, avoid tight coupling.
2. Phase 1: run fast local checks for every change.
3. Phase 2: add integration tests for data contracts and end-to-end tool flows.
4. Phase 3: add firmware/groundstation and hardware-in-the-loop test layers as implementation matures.

## Planned structure

- `tests/unit/`: unit tests that are not tied to a single package.
- `tests/integration/`: multi-module and contract-flow tests.
- `tests/fixtures/`: shared static inputs (small logs, sample messages, configs).
- `tests/hil/`: optional hardware-dependent tests (later).

Package-local tests can still live with the package when that is the clearest location (example: `tools/usv_sim/tests`).

## Conventions (to keep consistency)

- Use `test_*.py` naming.
- Keep tests deterministic (no network, wall-clock timing dependencies, or hardware requirements by default).
- Prefer small, focused tests over large scenario scripts.
- Put shared test data in `tests/fixtures/` instead of duplicating across folders.

## Future run targets

When we formalize CI, we should expose one clear command entrypoint from repo root that runs:

- docs checks
- package unit tests
- integration tests (when present)

This file is the policy baseline for that future setup.
