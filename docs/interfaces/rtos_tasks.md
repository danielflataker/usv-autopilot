# RTOS tasks (V1)

This page sketches the RTOS task split and the data paths between tasks. The goal is “no blocking in control” and clear ownership.
Final rates/priorities should be tuned after bring-up.

See also: [dataflow.md](dataflow.md) and [contracts.md](contracts.md).

## Proposed V1 task set

### 1) Control loop task (highest priority)
Purpose: deterministic loop for estimation + guidance + control + actuator output.
Typical rate: 50–200 Hz.

Does:
- run EKF predict each tick using $\Delta t$
- apply any pending measurement updates (see “Estimator placement” below)
- run mission/guidance (if autopilot enabled)
- run controllers + actuator shaping
- write final `ESC_OUTPUT` (non-blocking)
- publish latest-value snapshots (`NAV_SOLUTION`, `GUIDANCE_REF`, `ACTUATOR_REQ`, `ACTUATOR_CMD`) via mailbox
- push log records into a ringbuffer (non-blocking)

Must never:
- block on SD, telemetry, printing, or slow drivers

### 2) Sensor I/O task (high priority, but below control)
Purpose: read sensors, timestamp, and publish raw measurements.
Typical: event-driven + small periodic poll.

Does:
- read IMU at its native rate (often > control rate)
- read GNSS messages (UART stream)
- optional mag/baro, etc.
- attach timestamp `t_us`
- push `meas_*` messages to an estimator input queue (or write “latest sample” structs)

### 3) Telemetry task (medium priority)
Purpose: send downlink snapshots + events without blocking control.
Typical: 5–20 Hz snapshot + immediate events.

Does:
- read latest-value mailboxes (pose/status) and send at a fixed rate
- read an event queue and send events ASAP (mode switch, failsafe, param ack, rejects)
- rate limit low-priority streams

Notes:
- telemetry should not depend on SD logging (separate queues/buffers)

### 4) Logging task (low priority)
Purpose: write logs to SD (or other storage) from a ringbuffer.
Typical: batch writes (e.g. 5–20 Hz flush), large contiguous writes.

Does:
- drain `log_record_t` ringbuffer
- write to file(s)
- handle session folder + metadata
- report overflow counters / write errors as events

### 5) Housekeeping task (optional, low priority)
Purpose: slow “system management”.
Typical: 1–10 Hz.

Examples:
- battery/voltage monitor and low-battery logic
- buzzer/beep patterns
- LED status
- periodic stats (CPU load, buffer watermarks)

(These can also be timer callbacks if trivial, but keep them out of control.)

## Estimator placement
Plan for V1:
- EKF predict runs in the control loop (fixed $\Delta t$).
- Sensor reads are asynchronous; each measurement is queued with timestamp.
- Control loop consumes all queued measurements since last tick and applies EKF updates in timestamp order.

Why:
- keeps one place responsible for state + covariance
- avoids race conditions and “half-updated” states
- easy to keep estimator always-on in all modes

Alternatives (possible later):
- run estimator update as a callback in the sensor task (harder to keep consistent state unless locking is heavy)
- make estimator its own task (works, but then control must consume snapshots; adds latency/complexity)

## Watchdog / heartbeat (notes)
- A hardware watchdog is usually worth adding once motors are running.
- It does not need a big task: kick it from the control task *only if* key health conditions are met (no overruns, sensors alive, etc.).
- Heartbeat for telemetry is separate: telemetry task should send a heartbeat at a fixed rate.

## Buffers / IPC (V1)
- Mailboxes for latest-value signals: `NAV_SOLUTION`, `GUIDANCE_REF`, `ACTUATOR_REQ`, `ACTUATOR_CMD`
- Event queue for sparse events (mode changes, param updates, rejects)
- Ringbuffer for high-rate logging (producer: control loop, consumer: logging task)
- Optional: separate small “priority event” queue to telemetry (so events don't wait behind bulk data)

## TODO / Open questions
- Final loop rates and priority ordering (after first bring-up)
- Measurement timestamping strategy (single monotonic `t_us` source)
- What happens on overload: drop logs first, then low-priority telemetry, never block control
- Is a dedicated RC input task needed, or should RC stay in sensor I/O?
