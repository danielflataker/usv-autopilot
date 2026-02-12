# Ops: Troubleshooting

## Purpose
A short playbook for diagnosing common failures without guesswork.

## Goals
Symptom-driven guidance:
- what is observed
- likely causes
- quick checks
- next actions

## Things to think about
- Power: resets, brownouts, noisy rails, ground loops
- Sensors: no data, wrong axis/units, drift/outliers
- Control: oscillations, slow response, saturation, sign errors
- Comms: packet loss, framing errors, desync, wrong baud
- Logging: SD stalls, buffer overruns, corrupted sessions

## Open questions
- Standard “debug snapshot” to capture when issues happen
- Where to record known-good wiring/config references
- How to escalate from bench → water test → hardware inspection
