# Roadmap

This project is developed one working step at a time, based on what we learn from the real boat.

## Hardware bring-up

Bring up the STM32, sensors, RC input and both motor outputs.

**Goal:** the complete manual-control path works reliably on the bench.

## Manual water testing

Run the boat manually and record useful sensor and actuator data.

**Goal:** produce real data that can be plotted and used to guide further development.

## Heading control

Estimate heading and yaw rate, then add autonomous heading control using differential thrust.

**Goal:** the boat can hold and change heading reliably.

## State estimation

Fuse the available sensor measurements into one consistent navigation state.

**Goal:** control and guidance use a reliable estimate of the boat's motion.

## Waypoint guidance

Add LOS guidance and simple waypoint progression.

**Goal:** the boat can follow a short waypoint mission with manual takeover available.

## Later

Add features such as MAVLink/QGroundControl, onboard logging and improved actuator handling only if they become useful.