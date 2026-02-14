# ADR 0002: QGC-first strategy for ground operations (V1)

## Status
Proposed (pending team sign-off)

## Context

We need to prioritize limited development time and maximize useful field capability early.

The current docs already lean toward using predefined MAVLink messages for V1 telemetry,
with custom messages only where project-specific data cannot be represented cleanly.
Mission upload protocol details are still open.

At the same time, a custom ground station is attractive for rich project-specific plots
(e.g., estimator internals and debug overlays), but this is not required to safely run
basic field missions if robust logs are available for post-run analysis.

## Decision

For V1 and near-term milestones, we propose a **QGC-first** strategy:

1. Prioritize compatibility with existing MAVLink ground control software
   (QGroundControl first, optionally Mission Planner for cross-checks).
2. Treat the in-repo custom ground station as a **de-prioritized / optional** track for
   advanced visualizations and project-specific diagnostics (not removed).
3. Focus implementation on the standard MAVLink mission/parameter/command flows
   needed for practical planning, upload, execution control, and status visibility.

## Consequences

### Positive
- Fastest path to usable mission planning and operations with mature tools.
- Lower maintenance burden in early phases.
- Easier interoperability testing against common MAVLink clients.

### Trade-offs
- Some project-specific UX and advanced custom plots will be deferred.
- We must align behavior with MAVLink client expectations and edge cases.

## Required MAVLink support baseline (V1)

Telemetry baseline (already aligned in docs):
- `HEARTBEAT`
- `SYS_STATUS`
- `ESTIMATOR_STATUS`
- `LOCAL_POSITION_NED`
- `ATTITUDE`
- `STATUSTEXT`
- `PARAM_VALUE` + core parameter flow (`PARAM_REQUEST_LIST`, `PARAM_REQUEST_READ`, `PARAM_SET`)
- `PARAM_EXT_ACK` only if extended parameter semantics are needed

Mission planning/control baseline:
- `MISSION_COUNT`
- `MISSION_REQUEST_INT` (prefer `*_INT` path)
- `MISSION_ITEM_INT`
- `MISSION_ACK`
- `MISSION_REQUEST_LIST` (required for mission readback/download)
- `MISSION_REQUEST` + `MISSION_ITEM` fallback handling for non-INT mission clients
- `MISSION_CLEAR_ALL`
- `MISSION_SET_CURRENT`
- `MISSION_CURRENT` (status)
- `MISSION_ITEM_REACHED` (status/event)

For V1, support both mission upload and mission readback flows so QGC can verify
downloaded mission contents after upload.

Vehicle command baseline:
- `COMMAND_LONG` handling for start/stop/safety-relevant control actions used by GCS
- `COMMAND_ACK`

Parameter baseline:
- `PARAM_REQUEST_LIST`
- `PARAM_REQUEST_READ`
- `PARAM_SET`
- `PARAM_VALUE`

## Implementation notes

- Use predefined MAVLink messages whenever semantically acceptable.
- Keep custom messages only for structured internal debug payloads.
- Validate compatibility with QGC first; add a second client check when practical.

## Follow-up

- Keep custom ground station docs but mark as non-blocking for V1 operations.
- Add a concrete compatibility checklist under `docs/comms/` and track in milestones.
