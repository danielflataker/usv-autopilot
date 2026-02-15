# Dataflow (V1)

This page describes who produces what, and how data moves through the firmware at runtime.
It complements [contracts.md](contracts.md) by showing the pipeline.

## Canonical topics (publish -> consume)
(Topic names are logical; actual RTOS wiring may differ.)

- `NAV_SOLUTION` (`nav_solution_t`)
  - publish: estimator
  - consume: guidance, control, logging, telemetry

- `MISSION_STATE` (`mission_state_t`)
  - publish: mission manager
  - consume: LOS guidance, speed scheduler, telemetry/logging (debug)

- `GUIDANCE_REF` (`guidance_ref_t`)
  - publish: guidance (LOS + speed scheduler)
  - consume: controller, logging, telemetry

- `ACTUATOR_REQ` (`actuator_req_t`)
  - fields: `u_s_req`, `u_d_req`, `src` (+ validity/timestamp)
  - publish: controller or RC mapping (mode-dependent)
  - consume: command shaping, logging (optional)

- `ACTUATOR_CMD` (`actuator_cmd_t`)
  - fields: `u_s_cmd`, `u_d_cmd` (+ validity/timestamp)
  - publish: command shaping
  - consume: allocator/mixer, logging (optional)

- `MIXER_FEEDBACK` (`mixer_feedback_t`)
  - fields: `u_s_ach`, `u_d_ach`, saturation flags (+ timestamp)
  - publish: allocator/mixer
  - consume: controllers (anti-windup), logging (optional)

- `ESC_OUTPUT` (`esc_output_t`)
  - publish: allocator/mixer
  - consume: ESC driver

## Timing model (V1)
- Control loop runs at a fixed rate (e.g. 50–200 Hz)
- Estimator predict runs in the control loop; measurement updates happen when new sensor data arrives
- Guidance runs in the control loop (cheap computations)
- Logging/telemetry are best-effort and must not block control

## Ownership rules (keep simple)
- Estimator owns state estimation and health flags
- Mission manager owns waypoint switching
- LOS owns $\psi_d$ and geometry errors
- Speed scheduler owns $v_d$ ramping and speed caps
- Controller/RC mapping owns source request generation $(u_s^{req},u_d^{req})$
- Command shaping owns scaling/deadband/expo + command-envelope clamp $(u_s^{req},u_d^{req}) \rightarrow (u_s^{cmd},u_d^{cmd})$
- Allocator/mixer owns feasibility policy + mapping to `u_L,u_R`

## Transport between modules/tasks
Within the same task:
- plain function calls + stack/local structs (no queues)

Across tasks (V1):
- Mailboxes for latest-value signals (e.g. `NAV_SOLUTION`, `GUIDANCE_REF`)
- Events use a single emit API with fanout:
  - producers call `event_emit(event_t)`
  - the event bus/router writes to two queues:
    - `event_q_sd` (consumer: logging task -> `events.jsonl`)
    - `event_q_tm` (consumer: telemetry task)
- Ringbuffer for high-rate time series logs (producer: control loop, consumer: SD writer)

Rule: control loop must never block. On overflow, drop and count (per-buffer counters).

## TODO / Open questions
- Exact loop rates and where each topic is produced (same task vs cross-task)
- Which signals are “log-only” vs “telemetry snapshot” vs “events”
- Minimal set of debug fields that help tuning without bloating structs