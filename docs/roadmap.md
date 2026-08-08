# Roadmap

This project is developed one working step at a time, based on what we learn from the real boat.

Milestones describe stable project stages. Detailed issues are created only as each stage approaches, so the roadmap can show the intended direction without over-planning the implementation.

## M1 — Hardware bring-up

Bring up the STM32, sensors, RC input and both motor outputs.

**Goal:** the complete manual-control path works reliably on the bench.

## M2 — Manual water testing

Operate the boat manually on water and collect useful sensor and actuator data.

**Goal:** establish a real baseline dataset for estimation and control development.

## M3 — State estimation

Fuse the available sensor measurements into one consistent navigation state.

**Goal:** provide a reliable state estimate for control and guidance.

## M4 — Control & allocation

Track heading and speed references and map control commands to feasible left and right motor outputs.

**Goal:** the boat can regulate heading and speed while respecting the forward-only actuator limits.

## M5 — Waypoint guidance

Generate heading and speed references from waypoints using simple LOS guidance and waypoint progression.

**Goal:** the boat can follow a short waypoint route with manual takeover available.

## M6 — Telemetry & ground station

Add MAVLink, SiK and QGroundControl support for mission upload, status and essential tuning.

**Goal:** missions can be uploaded and the autonomous system can be monitored from shore.

## M7 — Field validation & tuning

Run repeatable autonomous tests and use logged data to improve estimation, control and safety behaviour.

**Goal:** the boat completes repeatable waypoint missions with reliable manual takeover.

## M8 — Final demonstration

Clean up and document the system once the main functionality has been validated.

**Goal:** produce a stable, reproducible final demonstration of the complete autopilot.
