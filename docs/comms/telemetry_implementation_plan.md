# Telemetry Implementation Plan (V1)

Purpose: define a practical, testable path from current dummy telemetry tooling to real STM32 + SiK MAVLink telemetry.

## Current state

Implemented now:
- Dummy log generation (full process chain) via `tools/generate_dummy_logs.py`
- Shared log parsing via `tools/log_io/read_timeseries_bin()`
- MAVLink-aligned telemetry mapping (logical message objects) via `tools/log_io/telemetry.py`
- Dummy telemetry emitter CLI via `tools/emit_dummy_telemetry.py`
- Mapping decision doc: `mavlink_mapping.md`

Not implemented yet:
- Binary MAVLink encode/decode layer
- Real link transport adapter (serial/SiK)
- Groundstation backend integration
- Firmware telemetry sender parity checks

## Message policy (V1)

Predefined MAVLink messages:
- `HEARTBEAT`
- `SYS_STATUS`
- `ESTIMATOR_STATUS`
- `LOCAL_POSITION_NED`
- `ATTITUDE`
- `STATUSTEXT`
- `PARAM_EXT_ACK`

Custom messages (only if needed):
- `USV_EVENT`
- `USV_CTRL_DEBUG`
- `USV_MIXER_FEEDBACK`

Rule:
- Use predefined MAVLink wherever semantically acceptable.
- Add custom messages only for structured payloads that cannot be represented cleanly.

## Milestones

### M1: Stable logical telemetry model (done)
Acceptance:
- Dummy logs can be mapped into telemetry message objects.
- Mapping includes heartbeat, status, pose, events, and param-ack behavior.
- Unit tests pass for emitted message presence.

### M2: Binary MAVLink encoder/decoder (next)
Scope:
- Add a small adapter that converts telemetry message objects to binary MAVLink frames.
- Decode the same frames back to message objects for test/replay.
Acceptance:
- Round-trip test: object -> bytes -> object for V1 predefined messages.
- Byte stream is consumable by common MAVLink tooling.

### M3: Transport adapters (next)
Scope:
- Dummy transport adapter (loopback or UDP for local dev).
- Real serial adapter (SiK-style serial port).
Acceptance:
- Same telemetry core used by both adapters.
- Backend can switch transport by config, no message mapping changes.

### M4: Groundstation backend integration (next)
Scope:
- Backend receives MAVLink frames, decodes, publishes normalized telemetry model to UI.
Acceptance:
- “No hardware” mode works using dummy telemetry stream.
- Basic UI fields update at expected rates (`POSE` 5 Hz, `HEARTBEAT/STATUS` 1 Hz).

### M5: Firmware parity and contract checks (later)
Scope:
- STM32 telemetry task emits matching message set.
- Add CI sync checks for record/message IDs where relevant.
Acceptance:
- Same backend can ingest both dummy and real telemetry without codepath forks.

## Open decisions

- Whether to include local `(x,y)` only or also lat/lon in V1 telemetry.
- Whether `CTRL` remains custom-only or partially mapped to predefined MAVLink fields.
- How much reliable delivery is needed beyond best-effort telemetry (commands/params handled separately).

