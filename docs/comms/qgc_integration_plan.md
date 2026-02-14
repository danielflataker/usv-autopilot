# QGC Integration Plan (V1)

Purpose: define the minimum MAVLink compatibility needed to use QGroundControl as the primary mission-planning and field-operations ground station.

## Scope

- Mission planning/upload/download compatibility
- Parameter sync/edit compatibility
- Basic command/control compatibility
- Telemetry visibility needed for field operations

Non-goals (V1):
- Full parity with ArduPilot/PX4 feature surface
- Custom in-house UI features for deep debug plotting

## Message checklist

### 1) Core heartbeat/status

Required:
- `HEARTBEAT`
- `SYS_STATUS`
- `STATUSTEXT`

Recommended:
- stable autopilot/type/mode signaling in `HEARTBEAT`
- regular cadence (e.g., 1 Hz status baseline)

### 2) Pose / estimator visibility

Required:
- `LOCAL_POSITION_NED`
- `ATTITUDE`

Recommended:
- `ESTIMATOR_STATUS`
- optional global position message path when map UX needs it

### 3) Mission protocol (primary)

Required (V1 baseline):
- Upload path: `MISSION_COUNT`, `MISSION_REQUEST_INT` (or `MISSION_REQUEST` fallback), `MISSION_ITEM_INT`, `MISSION_ACK`
- Readback path: `MISSION_REQUEST_LIST`, `MISSION_COUNT`, `MISSION_REQUEST_INT`/`MISSION_REQUEST`, `MISSION_ITEM_INT`/`MISSION_ITEM`, `MISSION_ACK`
- Control path: `MISSION_CLEAR_ALL`, `MISSION_SET_CURRENT`

Strongly recommended:
- Status path: `MISSION_CURRENT`, `MISSION_ITEM_REACHED`

Notes:
- Prefer `*_INT` mission item path for waypoint precision/compatibility, but be robust to clients that use non-INT fallback.
- Treat mission transactions as reliable with clear timeout/retry behavior.
- Mission upload **and** readback are both required for V1 and are validated explicitly in acceptance criteria below.

### 4) Parameter protocol

Required:
- `PARAM_REQUEST_LIST`
- `PARAM_REQUEST_READ`
- `PARAM_SET`
- `PARAM_VALUE`

Optional/advanced:
- `PARAM_EXT_*` where long strings/types are needed
- Do not require `PARAM_EXT_*` for V1 unless a specific GCS flow depends on it

Notes:
- Parameter names are project-defined; protocol is standardized.
- Expose only parameters safe for field tuning in V1, gate unsafe writes by mode/armed state.

### 5) Command protocol

Required:
- `COMMAND_LONG`
- `COMMAND_ACK`

Recommended:
- support a minimal set of commands needed for arm/disarm/start/stop and mission control semantics used by chosen GCS workflow

## Validation plan

1. Bench test with QGC connected over simulated link.
2. Verify end-to-end mission upload, readback, start, progress, and completion.
3. Verify parameter list retrieval and single-parameter set/apply with acknowledgment.
4. Verify command acknowledgments and negative paths (unsupported/denied).
5. Repeat smoke test with one alternate client (optional but recommended).

## Acceptance criteria (V1, QGC-first, mission readback is required)

- QGC can upload and read back missions without custom tooling.
- QGC can display live vehicle status/pose at expected update rates.
- QGC can list and set exposed parameters with clear acknowledgments.
- Command/control interactions used in field test workflow are acknowledged deterministically.
- Custom ground station is not required for normal field operation.
