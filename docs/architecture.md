# Architecture (Software + Sensor Stack)

## Scope
Runtime architecture, module boundaries, and task/IPC patterns for the USV autopilot on STM32 + FreeRTOS.

Deep dives live elsewhere:
- Interfaces/contracts: [interfaces/contracts.md](interfaces/contracts.md)
- RTOS layout: [interfaces/rtos_tasks.md](interfaces/rtos_tasks.md)
- Dataflow/IPC: [interfaces/dataflow.md](interfaces/dataflow.md)
- Estimation: [estimation/overview.md](estimation/overview.md)
- Guidance: [guidance/overview.md](guidance/overview.md)
- Control: [control/overview.md](control/overview.md)
- Logging: [logging/overview.md](logging/overview.md)
- Comms/telemetry: [comms/overview.md](comms/overview.md)

## System overview (STM32)

### Main tasks (V1)
- `task_control` — deterministic loop (estimation + guidance + control + actuation)
- `task_sensors` — sensor I/O (IMU, GNSS, RC), timestamping, publish latest/queue measurements
- `task_telemetry` — downlink snapshots + events (best-effort, rate-limited)
- `task_logger` — SD writes (drains ringbuffers, creates session folder/files)
- `task_housekeeping` — slow supervision (battery, buzzer/LED, stats), optional

(Exact split and rates are defined in [interfaces/rtos_tasks.md](interfaces/rtos_tasks.md).)

## Control loop pipeline (`task_control`)
Each tick runs without blocking:

1) **Snapshot inputs**
- pull latest-value buffers (RC state, mission state, etc.)
- pull queued sensor measurements since last tick (timestamped)

2) **State estimation (always-on)**
- EKF predict each tick
- apply measurement updates in timestamp order when available
- publish `nav_solution_t` (see [interfaces/contracts.md](interfaces/contracts.md))

3) **Mode manager**
- select active mode: `IDLE`, `MANUAL`, `AUTOPILOT`, `TESTS`, `ABORT`
- modes implement `enter()/update()/exit()`
- transitions emit events (via `event_emit()`)

4) **Autopilot (only if mode enables it)**
- `mission_manager`: active segment + waypoint switching
- `los_guidance`: compute lookahead target → desired heading `psi_d` + errors (`e_y`, `e_psi`)
- `speed_scheduler`: start from segment speed `v_seg`, apply caps (WP proximity, |e_psi|, …), then ramp → `v_d`
- `control_cascade`: heading loop (`e_psi` → `r_d`) + yaw-rate loop (`e_r` → `u_d`/`DeltaT`) + speed loop (`e_v` → `u_s`/`T`)

5) **Actuator shaping + ESC output**
- clamp/deadband/slew-rate limiting
- differential thrust mixing → per-motor `u_L`, `u_R`
- write to ESC output (non-blocking)

6) **Log + event emission**
- push high-rate records to the log ringbuffer (non-blocking)
- emit sparse events via `event_emit()` (mode switches, param apply, gating, …)

## IPC patterns (V1)
- **Mailboxes**: latest-value signals (`NAV_SOLUTION`, `GUIDANCE_REF`, status snapshots)
- **Measurement queue**: timestamped sensor measurements → estimator update path
- **Ringbuffer**: high-rate log records → `task_logger`
- **Event bus**: producers call `event_emit(event_t)`; implementation fans out to:
  - `event_q_sd` (consumer: `task_logger` → `events.jsonl`)
  - `event_q_tm` (consumer: `task_telemetry`)
Drop-on-full is allowed; counters must be logged.

Details: [interfaces/dataflow.md](interfaces/dataflow.md)

## Sensors (V1)
- IMU: high rate (typically > control rate), timestamp close to acquisition
- GNSS: lower rate, timestamp on parse/arrival
- Heading strategy (MVP): gyro-propagated yaw, optionally corrected by COG when speed > threshold; mag is optional (EMI dependent)

## Logging (SD)
Session folder per run:
- `meta.json` (includes `git_sha`, `git_dirty`, build info, params snapshot)
- `timeseries.bin` (high-rate binary record stream)
- `events.jsonl` (sparse events)

Logging is best-effort; SD latency must never stall control.
Details: [logging/overview.md](logging/overview.md), [logging/record_formats.md](logging/record_formats.md), [logging/events.md](logging/events.md)

## Telemetry (SiK)
Telemetry must not depend on SD logging.
- snapshots: latest pose/status at a modest rate (UI can interpolate)
- events: sparse queue, sent ASAP
Transport/protocol is described in [comms/protocol.md](comms/protocol.md) (MAVLink vs custom is a separate decision).

## Parameters
- on-water updates via a “commit/apply” model (batch apply preferred)
- parameter changes are logged as events, and stored in `meta.json` (snapshot or hash)
Apply rules and wire format live in [comms/params.md](comms/params.md)

## Conventions
- time: monotonic microseconds `t_us`
- units: SI (m, rad, m/s, rad/s)
- coordinate frame conventions are defined here (and referenced everywhere):
  - **TODO:** pick ENU vs NED and sign convention for `psi` and stick to it globally
