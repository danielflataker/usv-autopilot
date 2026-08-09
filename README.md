# USV Autopilot

A small STM32-based autopilot project for a twin-propeller catamaran.

The goal is to learn and demonstrate the core parts of an autonomous marine control system on real hardware: sensing, state estimation, feedback control and waypoint guidance.

## Main goals

- Read IMU and GNSS data on the STM32.
- Keep manual RC control available for testing and takeover.
- Estimate the boat state from onboard sensors.
- Control heading and speed using differential thrust.
- Follow waypoint paths using simple LOS guidance.
- Log enough data to understand and tune the system.

The two ESCs are forward-only, so differential thrust is constrained by the available motor range. The first implementation will keep this explicit and simple, then add more advanced limiting or anti-windup only if testing shows that it is needed.

## System overview

```text
IMU + GNSS
    |
    v
State estimation
    |
    v
LOS guidance
    |
    v
Heading / speed control
    |
    v
Differential-thrust mixer
    |
    v
Left + right motor
```

## Current focus

The project is starting with hardware bring-up and manual testing. Autonomous control will be added one working step at a time.

See [docs/roadmap.md](docs/roadmap.md) for the project roadmap, [hardware/README.md](hardware/README.md) for the current hardware baseline, and [docs/workflow.md](docs/workflow.md) for the lightweight Git workflow.

## Repository

As implementation starts, the repository will mainly contain:

- `hardware/` — hardware architecture, wiring and integration
- `firmware/` — STM32 firmware
- `analysis/` — small Python scripts for plotting and test analysis
- `docs/` — short documentation for the system that actually exists

The project intentionally keeps the software structure small and explicit. New abstractions and infrastructure should be added only when the implementation gives a clear reason for them.

Generated build output and local workspace files are ignored, while source code and project configuration needed to build the firmware belong in the repository.
