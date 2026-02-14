# Logging Contract Sync Checklist

Purpose: keep firmware logging structs/enums and Python parsing layout aligned without introducing runtime schema parsing on STM32.

## Source of truth (current)

- Python tooling contract: `tools/log_io/layout.py`
- Firmware contract: C enums/structs in firmware logging headers (to be added)
- Compatibility gate: `FW_MODEL_SCHEMA`

## Rules

1. STM32 runtime does not parse JSON/YAML.
2. Firmware keeps hardcoded enums/structs for determinism.
3. Python parser/generator uses `tools/log_io/layout.py`.
4. Breaking payload/field/order change requires `FW_MODEL_SCHEMA` bump.
5. Additive new record IDs are backward compatible (parser skips unknown IDs).

## When changing a record

1. Update C enum/struct (firmware).
2. Update `tools/log_io/layout.py`.
3. Update parser tests (`tools/usv_sim/tests/test_log_io.py` and contract sync tests).
4. If breaking, bump `FW_MODEL_SCHEMA` in firmware and Python.
5. Regenerate dummy logs and verify parse succeeds.

## CI intent

- Run parser unit tests on every PR.
- Add a firmware-to-python contract comparison test when firmware logging headers are present.
