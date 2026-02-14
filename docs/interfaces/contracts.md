# Contracts (interfaces)

Purpose: define the internal software contracts inside the firmware (and any shared code).
This is the canonical place for shared structs, enums, and module APIs.

If a type crosses a module/task boundary, it should be defined here (or referenced from here).

## Scope
- Firmware-internal contracts (estimation, guidance, control, modes, logging, comms)
- Shared types with the ground station *only if* they must match bit-for-bit

Non-goals:
- Full implementations
- HAL/driver details

## Pipeline contracts (topics → payload types)

To make the dataflow explicit, we name the *thing being published* (topic) and the struct that carries it:

- `NAV_SOLUTION` → `nav_solution_t`
- `MISSION_STATE` → `mission_state_t`
- `GUIDANCE_REF` → `guidance_ref_t`
- `ACTUATOR_CMD` → `actuator_cmd_t`
- `MIXER_FEEDBACK` → `mixer_feedback_t`
- `ESC_OUTPUT` → `esc_output_t`

(Exact RTOS wiring is described in [rtos_tasks.md](rtos_tasks.md) and [dataflow.md](dataflow.md).)

## Core data types (V1)

### Navigation / estimation
- `nav_solution_t` (published by estimator)
  - pose: `x, y, psi`
  - rates/speeds: `v, r`
  - gyro bias: `b_g`
  - health: `status flags` + optional covariance diag (TBD)
  - timestamp: `t_us`

### Mission management
- `mission_state_t` (published by mission manager)
  - `idx` (active segment: waypoint `idx` → `idx+1`)
  - `active`, `done`
  - segment endpoints: `x0,y0` and `x1,y1`
  - segment target speed: `v_seg` (optional in V1)
  - distance to next WP: `d_wp` (optional; can also be computed in guidance)
  - timestamp: `t_us`

### Guidance references
- `guidance_ref_t` (published by guidance)
  - desired heading: `psi_d`
  - desired speed (post scheduler): `v_d`
  - optional debug terms: `e_psi`, `e_y`, `v_cap` (keep optional to avoid bloat)
  - timestamp: `t_us`

### Control / actuation
- `actuator_cmd_t` (published by controller, consumed by mixer/limits)
  - canonical internal form: `u_s_cmd`, `u_d_cmd` (explicit command-stage names; preferred)
    - math form in this stage: $u_s^{cmd}, u_d^{cmd}$
    - `u_s_cmd` is commanded average thrust
    - `u_d_cmd` is commanded differential thrust (positive means $u_R > u_L$ after mixing)
  - validity flags (armed / failsafe)
  - timestamp: `t_us`

- `mixer_feedback_t` (published by mixer/limits, consumed by controllers for anti-windup)
  - achieved commands after mixing + clamping:
    - `u_s_ach`, `u_d_ach`
  - saturation flags:
    - `sat_L`, `sat_R`, `sat_any`
    - recommended extension: `sat_cmd_stage`, `sat_alloc`, `sat_motor_stage`
  - optional: `u_L_ach`, `u_R_ach` (only if needed for debugging/logging)
  - optional: effective limits used this cycle (`u_s_max_eff`, `u_d_max_eff`, `u_motor_max_eff`)
  - timestamp: `t_us`

Guideline for signal count (to avoid naming overload):
- Required for control: `u_*_cmd` and `u_*_ach`
- Optional for debugging only: intermediate allocator-stage terms (e.g. `u_*_alloc`)

- `esc_output_t` (final output to hardware)
  - per-motor commands: `u_L`, `u_R` (normalized internal convention, achieved after limits)
  - arm/disarm + output validity
  - timestamp: `t_us`

Notes:
- The controller should not need to know whether the ESC supports reverse. That mapping is owned by the ESC driver.
- For anti-windup, controllers should use `u_s_ach` / `u_d_ach` (or `sat_any`) rather than guessing limits.

## Modes / state machine
- `mode_t`: enum of modes (manual, autopilot, tests, abort, idle, ...)
- `mode_iface_t`: mode callbacks
  - `enter(ctx)`
  - `update(ctx, dt)` (produces either `guidance_ref_t` or `actuator_cmd_t`, depending on mode)
  - `exit(ctx)`

(Mode behavior is described in [modes.md](modes.md).)

## Inter-task messaging (payloads)
Typed payloads passed through queues/mailboxes:
- `log_record_t` (see [logging/record_formats.md](../logging/record_formats.md))
- `telemetry_snapshot_t`, `event_t` (see [comms/telemetry.md](../comms/telemetry.md))
- `param_update_t`, `param_ack_t` (see [comms/params.md](../comms/params.md))
- `mission_chunk_t` / `mission_cmd_t` (if mission upload handled on MCU)

## Compatibility / schema IDs (tiny but important)

Some data contracts must match exactly between firmware, logs, and analysis tools (e.g. state order, units, binary record layouts). To avoid silent mismatches, we define a small schema ID.

- `FW_MODEL_SCHEMA` (int): bumped only when a *breaking* contract change happens
  - examples: state vector order/meaning, frame conventions (ENU/NED), log binary layout, telemetry payload layout
  - non-examples: tuning changes, bugfixes, parameter tweaks

Where it shows up:
- Firmware: compiled constant (e.g. `#define FW_MODEL_SCHEMA 1`) and written into session `meta.json` / boot event
- Tools: `usv_sim.digital_twin.current.FW_MODEL_SCHEMA` and checked when loading a dataset

Recommended dataset check:
- analysis/parsers should fail fast if `dataset.schema != tool.schema`

## Event bus (contract)
Events are emitted at the source and may have multiple consumers (SD logging, live link, etc.).
Producers must not care who consumes the event.

- `event_t`: canonical event payload (see `logging/events.md` for semantics)
- `event_emit(const event_t* e)`: non-blocking
  - returns success/fail (or increments drop counters internally)
  - must be safe to call from the control loop

Implementation note (V1):
- `event_emit()` fans out to two queues:
  - `event_q_sd` (logging task)
  - `event_q_tm` (telemetry task)

Drop policy:
- never block the control loop
- drop on overflow and increment `event_drop_*` counters

## API conventions
- No dynamic allocation in control loop paths
- Prefer pure functions where possible (easy to test)
- If stateful, keep state in explicit `*_state_t` passed as pointer
- Time uses monotonic microseconds: `t_us`

Suggested function naming:
- `*_init`, `*_reset`
- `*_step` (stateful update each loop)
- `*_compute` (pure function if possible)

## TODO / Open questions
- Which fields in `nav_solution_t` are required for V1 telemetry vs log-only
- Do we keep `v_cap`/errors in `guidance_ref_t` or log them separately
- Should `mixer_feedback_t` always be published, or only when saturation occurs
- Which structs must be shared with the ground station (and versioned)
