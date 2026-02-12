# Ops: Bench tests

## Purpose
Quick, repeatable tests on the desk before going on water.

## Goals
Catch early issues:
- wiring/power mistakes
- sensor bring-up problems
- basic control output sanity
- logging/telemetry functioning

## Things to think about
- Minimal power-on checklist (rails, current draw, brownouts)
- Sensor sanity checks (IMU alive, GNSS messages, reasonable ranges)
- Telemetry link check (heartbeat, pose updates)
- Logging check (session folder created, files grow, no overruns)
- RC/manual override check and abort behavior
- “Dry-run” autopilot with motors disabled (actuator outputs only)

## Open questions
- What can be automated (self-test mode) vs done manually
- Pass/fail criteria and what gets logged as events
- Safety baseline (props off, motors disabled, clear labeling of test modes)
