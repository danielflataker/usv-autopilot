# Protocol (boat ↔ ground station)

This document describes **how messages are transported** between boat and ground station:
framing on serial, reliability/ACK rules, and multi-step transactions like mission upload.

Message *content* lives in `telemetry.md`. Parameter semantics live in `params.md`.

## Scope
- Serial framing (bytes on the wire)
- Sequencing, CRC, ACK/retry rules
- Mission upload transaction (start → chunks → commit)
- Resync after corruption / dropped bytes
- Versioning/compatibility

## Not in scope
- Telemetry fields and units (see `telemetry.md`)
- Ground station implementation details (see `docs/groundstation/`)

## TODO / Outline

### Protocol choice
- Decide: MAVLink (subset) vs custom framing
- Rationale + consequences (record as an ADR once chosen)

### Framing
- Header format (magic, msg type, length)
- Sequence number + timestamp (if any)
- CRC/checksum
- Max payload size and chunking rules

### Reliability rules
- Which messages are best-effort (telemetry)
- Which messages are reliable (mission upload, param apply, start/stop commands)
- ACK message format + timeout + retry count
- Duplicate detection (idempotency)

### Mission upload transaction
- `MISSION_BEGIN` (mission id, number of points, checksum)
- `MISSION_CHUNK` (index, payload)
- `MISSION_END` / `MISSION_COMMIT`
- Ack flow and resume behavior if interrupted

### Resync and robustness
- How receiver finds next valid frame after garbage bytes
- Behavior on CRC failure
- Rate limiting / backpressure

### Versioning
- Protocol version field in frames
- Forward/backward compatibility strategy
- What to do on version mismatch (reject with error)

## Open questions
- MAVLink: use existing mission/param messages, or define a small custom set anyway?
- Do we need reliable delivery for “start/stop/abort”, or do we rely on RC + failsafes?
- Is ground station required to handle partial mission resume, or is restart fine for V1?