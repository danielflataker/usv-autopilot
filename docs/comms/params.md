# Params (over telemetry)

This document defines the **parameter system over the link**: how parameters are named/identified, how updates are sent and applied, and how changes are acknowledged and logged.

This is about behavior and rules, not UI implementation details.

## Scope
- Parameter IDs/names, types, units, and limits
- Update flow (single-set vs batch, ack/fail)
- Apply rules (safe vs restricted, mode/armed constraints)
- Logging of parameter changes (events + snapshots)

## Not in scope
- Full ground station UI design (see `docs/groundstation/`)
- Internal controller math (see `docs/control/`)

## References
- Telemetry messages: `telemetry.md`
- Transport/framing: `protocol.md`
- Internal param structs: `../interfaces/contracts.md`

## TODO / Outline

### Parameter catalog
- Naming / IDs (string name or numeric ID)
- Type system (float, int, bool, enum)
- Units + min/max + default
- Grouping (control, guidance, EKF, safety, logging)

### Update messages
- `PARAM_SET` (single)
- `PARAM_SET_BATCH` (recommended default)
- `PARAM_GET` / `PARAM_LIST` (optional, but useful for UI sync)
- `PARAM_ACK` (seq + status + what was applied)

### Apply rules
- Safe-to-apply anytime vs restricted
- Mode/armed constraints (e.g. only in `IDLE/TESTS`, or only when thrust = 0)
- What happens on reject (keep old value, ack with error code)

### Rate limiting and dedupe
- UI can change values freely, but only commits should be sent
- Backend and/or firmware can rate-limit (e.g. max 1 Hz per param)
- Firmware should ignore “no-op” updates (new ~= old)

### Logging
- Log `PARAM_BATCH_APPLY(seq)` as an event
- Log individual `PARAM_SET(name/id, old, new)` (or only changed params)
- Save a full snapshot to `params.json` per session (and optionally per apply)

## Open questions
- Numeric ID vs string name on the wire?
- Do we need `PARAM_LIST` for auto-populating UI, or is the UI hardcoded for V1?
- Should restricted params be rejected outright, or queued until a safe state?