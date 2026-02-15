# Telemetry (messages and meaning)

This document defines what telemetry messages exist and what they mean: fields, units,
timestamps, frames, and recommended update rates.

How bytes are transported (framing/ACK) lives in [protocol.md](protocol.md).
Parameter update behavior lives in [params.md](params.md).

## Scope
- Message set (types + purpose)
- Field definitions + units
- Timestamp meaning (`t_us`)
- Coordinate frame conventions (for reported pose/heading)
- Recommended update rates and priorities

## Not in scope
- Transport/framing details (see [protocol.md](protocol.md))
- Ground station UI/server implementation (see `docs/groundstation/`)

## Conventions
- `t_us`: monotonic microseconds on the boat
- Units: SI (m, s, rad, m/s)
- Frames and angle/sign conventions: use canonical definitions in [architecture.md](../architecture.md)

## TODO / Outline

### Message types (V1)
- `HEARTBEAT` — system alive + mode + basic health
- `STATUS` — battery/voltage, sensor health flags, EKF health
- `POSE` — position + heading (+ optional velocity)
- `CTRL` (optional) — setpoints and outputs (e.g. $v_d$, $\psi_d$, $T$, $\Delta T$)
- `EVENT` — sparse events (mode switch, failsafe, test markers)
- `PARAM_ACK` — ack for parameter apply (seq + status)

### Field definitions (per message)
For each message type:
- required fields
- optional fields (V2+)
- units and valid ranges
- when it's sent (rate or event-triggered)

### Update rates / priority (recommendations)
- `POSE`: 2–10 Hz (default 5 Hz)
- `HEARTBEAT` / `STATUS`: 1 Hz
- `EVENT`: ASAP (queued)
- `PARAM_ACK`: ASAP after apply

### Timestamp and ordering
- `t_us` refers to time on boat at sample/apply time
- events should include `t_us` of when they happened (not when transmitted)

### Frame reporting
- Position: local NED $(x,y)$ as defined in [architecture.md](../architecture.md) (or lat/lon if V1 starts with that)
- Heading: $\psi$ as defined in [architecture.md](../architecture.md)
- If lat/lon is used, specify projection responsibility (boat vs ground)

## Open questions
- Send local $(x,y)$ only, or also lat/lon for easy map overlay?
- Include velocity in `POSE` for smoother UI interpolation?
- Is a dedicated `CTRL` message needed in V1, or is logging enough?
