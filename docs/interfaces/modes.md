# Modes (V1)

Modes define *who is in charge* of actuator commands at any time (manual vs autopilot vs tests vs abort).
This is a behavioral spec, not an implementation.

See also: [contracts.md](contracts.md) and [rtos_tasks.md](rtos_tasks.md).

## Mode list (initial)
- `IDLE`: motors off (or neutral), logging/telemetry still running
- `MANUAL`: RC passthrough (with safety limits)
- `AUTOPILOT`: mission + guidance + control
- `TESTS`: scripted maneuvers for identification (step, zigzag, turn, ...)
- `ABORT`: immediate safe behavior (e.g. neutral or predefined action)

(Exact list can change; keep the enum in `contracts.md` authoritative.)

## Ownership: who outputs what
- In `MANUAL`: mode outputs `esc_output_t` (or `actuator_cmd_t`) directly from RC inputs
- In `AUTOPILOT`: mode enables the pipeline (mission → guidance → control)
- In `TESTS`: mode bypasses mission/guidance and injects setpoints or actuator commands
- In `ABORT`: mode overrides everything and forces a safe output

## Mode interface (contract)
Each mode implements:
- `enter(ctx)`: initialize internal state, reset ramps/integrators as needed
- `update(ctx, dt)`: compute outputs for this cycle
- `exit(ctx)`: cleanup, stop timers, freeze logs if needed

## Common rules (V1)
- Only one mode is allowed to “own” actuation at a time
- Mode changes are logged as events (with from/to + reason)
- Switching into `AUTOPILOT` should reset guidance state (segment index, speed ramp) unless specified otherwise.

## Estimator always-on (V1)
The estimator runs in all modes:
- so the solution is “warm” when switching into `AUTOPILOT`
- so the ground station can show position/heading even in `MANUAL`/`IDLE`
- so logs are comparable across modes

Modes may choose to ignore estimator outputs for control, but `NAV_SOLUTION` is still produced continuously.

## TODO / Open questions
- What is the safe behavior in `ABORT` (neutral vs hold heading vs stop)?
- Should `TESTS` be one mode with sub-tests, or multiple modes?
- What conditions force mode changes (RC switch, link loss, EKF unhealthy, geofence)?