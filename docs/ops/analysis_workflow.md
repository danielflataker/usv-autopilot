# Ops: Analysis workflow

## Purpose
A lightweight, repeatable workflow for turning a log session into plots and conclusions.

## Goals
- Identify what happened during a run (modes/tests/waypoints)
- Compare runs across firmware versions and parameter sets
- Extract the few metrics needed for tuning (EKF + LOS + PID)

## Things to think about
- Always start by reading `meta.json` (git hash + dirty flag + params snapshot)
- Standard “session summary” plot set (pose, heading, speed, setpoints, actuator)
- Use events to slice runs (mode changes, test start/stop, WP switches)
- Keep a consistent time base (`t_us`) and document any wall-time mapping (if used)
- Decide where analysis code lives (repo folder + naming + minimal dependencies)

## Open questions
- Preferred output format (notebooks vs scripts that dump PNG/PDF)
- Minimal EKF tuning metrics (innovations/NIS, gating counts, bias drift)
- Where derived results live (e.g. `results/` inside the session folder)
