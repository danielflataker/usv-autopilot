# USV Autopilot — Docs Index

This folder is the source of truth for project architecture, module contracts, logging/telemetry formats, and test procedures.

## Start here
- System overview: [architecture.md](architecture.md)
- Vocabulary / symbols: [glossary.md](glossary.md)
- Interfaces and contracts (authoritative): [interfaces/contracts.md](interfaces/contracts.md)
- Run modes + RTOS tasks: [interfaces/modes.md](interfaces/modes.md), [interfaces/rtos_tasks.md](interfaces/rtos_tasks.md)
- On-water workflow: [ops/water_test_playbook.md](ops/water_test_playbook.md)

## Core topics

### Estimation
- Overview: [estimation/overview.md](estimation/overview.md)
- EKF design: [estimation/ekf_design.md](estimation/ekf_design.md)
- Process model: [estimation/process_model_v1.md](estimation/process_model_v1.md)
- Measurement models: [estimation/measurement_models.md](estimation/measurement_models.md)
- Tuning + gating: [estimation/tuning.md](estimation/tuning.md)
- Failure modes: [estimation/failure_modes.md](estimation/failure_modes.md)

### Guidance
- Overview: [guidance/overview.md](guidance/overview.md)
- Mission manager: [guidance/mission_manager.md](guidance/mission_manager.md)
- LOS guidance: [guidance/los_guidance.md](guidance/los_guidance.md)
- Speed scheduler: [guidance/speed_scheduler.md](guidance/speed_scheduler.md)

### Control
- Overview: [control/overview.md](control/overview.md)
- Cascaded heading/yaw-rate control: [control/cascaded_heading_yawrate.md](control/cascaded_heading_yawrate.md)
- Speed controller: [control/speed_controller.md](control/speed_controller.md)

### Actuation
- Command shaping: [actuation/command_shaping.md](actuation/command_shaping.md)
- Mixer + limits: [actuation/mixer_and_limits.md](actuation/mixer_and_limits.md)
- Actuation command pipeline spec: [actuation/actuation_command_pipeline_spec.md](actuation/actuation_command_pipeline_spec.md)

### Logging
- Overview: [logging/overview.md](logging/overview.md)
- Events: [logging/events.md](logging/events.md)
- Record formats: [logging/record_formats.md](logging/record_formats.md)

### Comms
- Overview: [comms/overview.md](comms/overview.md)
- Telemetry: [comms/telemetry.md](comms/telemetry.md)
- Parameters: [comms/params.md](comms/params.md)
- Protocol: [comms/protocol.md](comms/protocol.md)
- QGC integration plan: [comms/qgc_integration_plan.md](comms/qgc_integration_plan.md)

### Hardware notes
- Overview: [hw/overview.md](hw/overview.md)
- Wiring + power: [hw/wiring_power.md](hw/wiring_power.md)
- Waterproofing: [hw/waterproofing.md](hw/waterproofing.md)
- EMI notes: [hw/emi_notes.md](hw/emi_notes.md)

### Operations
- Water test playbook: [ops/water_test_playbook.md](ops/water_test_playbook.md)
- Bench tests: [ops/bench_tests.md](ops/bench_tests.md)
- Troubleshooting: [ops/troubleshooting.md](ops/troubleshooting.md)
- Log analysis workflow: [ops/analysis_workflow.md](ops/analysis_workflow.md)

### Interfaces (firmware)
- Overview: [interfaces/overview.md](interfaces/overview.md)
- Contracts: [interfaces/contracts.md](interfaces/contracts.md)
- Dataflow: [interfaces/dataflow.md](interfaces/dataflow.md)
- Modes: [interfaces/modes.md](interfaces/modes.md)
- RTOS tasks: [interfaces/rtos_tasks.md](interfaces/rtos_tasks.md)

### Ground station
- Overview: [groundstation/overview.md](groundstation/overview.md)
- Backend (Python): [groundstation/backend.md](groundstation/backend.md)
- Frontend (map/UI): [groundstation/frontend.md](groundstation/frontend.md)
- Data model: [groundstation/data_model.md](groundstation/data_model.md)
- Dev setup: [groundstation/dev_setup.md](groundstation/dev_setup.md)

## Decisions (ADRs)
- [adr/0001-workflow-and-docs.md](adr/0001-workflow-and-docs.md)
- [adr/0002-qgc-first-mavlink-strategy.md](adr/0002-qgc-first-mavlink-strategy.md)

## Conventions (quick)
- Timestamp: monotonic microseconds `t_us`
- Units: SI (m, s, rad, m/s)
- Coordinate frames: defined in [architecture.md](architecture.md)
- Writing style: imperative, pronoun-free, concise; use `*italics*` for rare callouts; avoid double-asterisk emphasis in body text.

## Planning
Implementation tasks are tracked in GitHub Issues + Projects (not in these docs).
