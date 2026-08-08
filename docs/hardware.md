# Hardware

This page tracks the hardware that is part of the working USV. Purchasing spreadsheets, prices, spare parts and components that are only being considered are kept outside the repository.

## Current baseline

| Part | Hardware | Role |
|---|---|---|
| Autopilot | STM32 Nucleo-H533RE | Main embedded controller |
| IMU | BMI270 breakout | Gyroscope and accelerometer |
| GNSS | u-blox NEO-M9N breakout | Position and velocity |
| RC receiver | FrSky RX8R Pro | Manual control and takeover |
| ESCs | 2 × Hobbywing Skywalker 60A | Motor control |
| Motors | 2 × SSS 2960 inrunner | Differential-thrust propulsion |

A SiK telemetry radio is available and may be added later if it is useful during testing.

## Actuation constraint

The current ESCs are treated as forward-only. With normalized surge and differential commands,

```text
left  = surge - yaw
right = surge + yaw
```

both motor commands must remain within the available forward range.

The first implementation will handle this directly at the motor mixer and keep the requested and achieved commands visible during testing. More advanced allocation or anti-windup will only be introduced if the measured behaviour justifies it.

## Updating this page

Keep this document about the hardware that is actually used in the system. Candidate components, order tracking and detailed purchasing information belong outside this repo.
