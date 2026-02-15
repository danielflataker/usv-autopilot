# Contracts (interfaces)

Purpose: define the internal software contracts inside the firmware (and any shared code).
This is the canonical place for shared structs, enums, and module APIs.

If a type crosses a module/task boundary, it is defined here (or referenced from here).

## Scope
- Firmware-internal contracts (estimation, guidance, control, modes, logging, comms)
- Shared types with the ground station *only if* they must match bit-for-bit

Non-goals:
- Full implementations
- HAL/driver details

## Pipeline contracts (topics -> payload types)

To make dataflow explicit, name the *thing being published* (topic) and the struct that carries it:

- `NAV_SOLUTION` -> `nav_solution_t`
- `MISSION_STATE` -> `mission_state_t`
- `GUIDANCE_REF` -> `guidance_ref_t`
- `ACTUATOR_REQ` -> `actuator_req_t`
- `ACTUATOR_CMD` -> `actuator_cmd_t`
- `MIXER_FEEDBACK` -> `mixer_feedback_t`
- `ESC_OUTPUT` -> `esc_output_t`

(Exact RTOS wiring is described in [rtos_tasks.md](rtos_tasks.md) and [dataflow.md](dataflow.md).)

## Core data types (V1)

### Navigation / estimation
- `nav_solution_t` (published by estimator)
  - pose: `x, y, psi`
  - V1 scope: planar state only (no `z`)
  - rates/speeds: `v, r`
  - gyro bias: `b_g`
  - health: `status flags` + optional covariance diag (TBD)
  - timestamp: `t_us`

### Mission management
- `mission_state_t` (published by mission manager)
  - `idx` (active segment: waypoint `idx` -> `idx+1`)
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
- Space convention for actuation:
  - request space `R`: `req` stage only
  - hardware-normalized space `H`: `cmd`, `alloc`, `ach`, and motor commands
  - two bases exist inside `H`: surge/differential (`u_s,u_d`) and left/right (`u_L,u_R`)
  - anti-windup residual is defined in `H`

- Stage-to-topic convention:
  - request stage (`R`, surge/differential): `ACTUATOR_REQ`
  - command stage (`H`, surge/differential): `ACTUATOR_CMD`
  - feedback stage (`H`, surge/differential): `MIXER_FEEDBACK`
  - motor output stage (`H`, left/right): `ESC_OUTPUT`

- `actuator_req_t` (published by source logic, consumed by command shaping)
  - canonical request-stage fields: `u_s_req`, `u_d_req`
    - math form in this stage: $u_s^{req}, u_d^{req}$ in request space `R`
    - `u_s_req` is raw average request from controller or RC mapping
    - `u_d_req` is raw differential request (positive means right-turn demand)
  - source metadata: `src` (`ACT_SRC_AUTOPILOT`, `ACT_SRC_MANUAL`, `ACT_SRC_TEST`)
  - validity flags (armed / failsafe)
  - timestamp: `t_us`

- `actuator_cmd_t` (published by command shaping, consumed by allocator/mixer)
  - canonical command-stage fields: `u_s_cmd`, `u_d_cmd`
    - math form in this stage: $u_s^{cmd}, u_d^{cmd}$ in hardware-normalized space `H`
    - `u_s_cmd` is shaped average command after scaling/deadband/command-envelope clamp
    - `u_d_cmd` is shaped differential command after scaling/deadband/command-envelope clamp
  - shaping metadata (optional): `k_s_mode`, `k_d_mode`
  - validity flags (armed / failsafe)
  - timestamp: `t_us`

- `act_src_t` (request source enum)
  - `ACT_SRC_AUTOPILOT`
  - `ACT_SRC_MANUAL`
  - `ACT_SRC_TEST`

- `alloc_policy_t` (allocator policy enum)
  - `ALLOC_SPEED_PRIORITY`
  - `ALLOC_YAW_PRIORITY`
  - `ALLOC_WEIGHTED` (later)

- `mixer_feedback_t` (published by mixer/limits, consumed by controllers for anti-windup)
  - achieved surge/differential commands in hardware-normalized space:
    - `u_s_ach`, `u_d_ach`
  - saturation flags:
    - `sat_L`, `sat_R`, `sat_any`
    - optional extension: `sat_cmd_stage`, `sat_alloc`, `sat_motor_stage`
  - optional: `u_L_ach`, `u_R_ach` (motor-basis diagnostics)
  - optional: effective limits used this cycle (`u_s_max_eff`, `u_d_max_pos_eff`, `u_d_max_neg_eff`, `u_LR_max_eff`, `u_LR_min_eff`)
  - timestamp: `t_us`

Guideline for signal count (to avoid naming overload):
- Required for control: `u_*_req`, `u_*_cmd`, and `u_*_ach`
- Optional for debugging only: intermediate allocator-stage terms (e.g. `u_*_alloc`)

- `esc_output_t` (final output to hardware)
  - per-motor commands: `u_L`, `u_R` (hardware-normalized, left/right basis)
  - arm/disarm + output validity
  - timestamp: `t_us`

Notes:
- ESC reverse/non-reverse mapping is handled by the ESC driver, not by the controller.
- Anti-windup residual is computed in hardware-normalized space:
  - $(u_s^{ach} - u_s^{cmd})$, $(u_d^{ach} - u_d^{cmd})$
- If a controller integrates in request space, map residuals through the request<->command map before updating integrators.

## Modes / state machine
- `mode_t`: enum of modes (manual, autopilot, tests, abort, idle, ...)
- `mode_iface_t`: mode callbacks
  - `enter(ctx)`
  - `update(ctx, dt)` (produces `guidance_ref_t`, `actuator_req_t`, or direct test outputs depending on mode)
  - `exit(ctx)`

(Mode behavior is described in [modes.md](modes.md).)

## Inter-task messaging (payloads)
Typed payloads passed through queues/mailboxes:
- `log_record_t` (see [logging/record_formats.md](../logging/record_formats.md))
- `telemetry_snapshot_t`, `event_t` (see [comms/telemetry.md](../comms/telemetry.md))
- `param_update_t`, `param_ack_t` (see [comms/params.md](../comms/params.md))
- `mission_chunk_t` / `mission_cmd_t` (if mission upload handled on MCU)

## Compatibility / schema IDs (tiny but important)

Some data contracts must match exactly between firmware, logs, and analysis tools (e.g. state order, units, binary record layouts). To avoid silent mismatches, define a small schema ID.

- `FW_MODEL_SCHEMA` (int): bumped only when a *breaking* contract change happens
  - examples: state vector order/meaning, frame conventions (see [architecture.md](../architecture.md)), log binary layout, telemetry payload layout
  - non-examples: tuning changes, bugfixes, parameter tweaks

Where it shows up:
- Firmware: compiled constant (e.g. `#define FW_MODEL_SCHEMA 1`) and written into session `meta.json` / boot event
- Tools: `usv_sim.digital_twin.current.FW_MODEL_SCHEMA` and checked when loading a dataset

Recommended dataset check:
- analysis/parsers fail fast if `dataset.schema != tool.schema`

## Event bus (contract)
Events are emitted at the source and may have multiple consumers (SD logging, live link, etc.).
Producers must not care who consumes the event.

- `event_t`: canonical event payload (see [logging/events.md](../logging/events.md) for semantics)
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
- Should `v_cap`/errors stay in `guidance_ref_t`, or be logged separately
- Should `mixer_feedback_t` always be published, or only when saturation occurs
- Which structs must be shared with the ground station (and versioned)
