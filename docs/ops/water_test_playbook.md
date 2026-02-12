# Ops: Water test playbook

## Purpose
A minimal, repeatable on-water procedure to get useful data safely.

## Goals
- Safety first
- Structured tests for identification and tuning
- Consistent logging so runs are comparable

## Things to think about
- Pre-launch checklist (battery, watertight, GPS fix, link, abort switch)
- Session structure: one session per parameter set vs param-change events
- Standard test sequence (idle drift, straight line, turns, zigzag, stop/go)
- Clear abort criteria (link loss, EKF unhealthy, low battery)
- Manual notes during testing (wind/current, anomalies, location)

## Open questions
- Minimum crew roles (pilot vs laptop/operator)
- How to label tests in logs (events vs separate sessions)
- How to handle retries when conditions change (wind/current)
