# Mixer and limits (V1)

This document defines how the controller outputs are turned into left/right motor commands,
and which limits are applied to keep the system safe and predictable.

## Goal
Convert total thrust $T$ and differential thrust $\Delta T$ into motor commands $(u_L, u_R)$,
then apply shaping (clamp/deadband/slew) before writing to the ESCs.

## Inputs / outputs
- Inputs: $T$, $\Delta T$, (optional) trims, limits, $dt$
- Output: $u_L$, $u_R$ (normalized motor commands or PWM targets)

## Core mapping
- Mixing:
  - $u_L = T - \Delta T$
  - $u_R = T + \Delta T$

(If you use sum/difference notation internally, document the mapping here once and stick to it.)

## Limits / shaping (order)
1) Optional trims/calibration
2) Clamp to allowed range
3) Deadband (optional)
4) Slew-rate limiting (rate of change)
5) Final write to ESC output (non-blocking)

## TODO / Outline

### 1) Command representation
- Decide: normalized $u \in [-1,1]$ vs $[0,1]$ vs PWM microseconds
- Define neutral/idle behavior (what is “stop”?)

### 2) Saturation
- Define $u_{\min}$, $u_{\max}$ (and whether reverse is allowed)
- Decide if clamp is symmetric (same forward/reverse) or not

### 3) Deadband
- Whether to include a deadband around zero
- Handling of ESC arming thresholds / minimum effective thrust

### 4) Slew-rate limiting
- Rate limits: $\dot u_{\max}$ up and down (may differ)
- Ensure this runs on $u_L/u_R$ after mixing

### 5) Safety gating
- What happens in each mode (MANUAL/AUTOPILOT/ABORT)
- Hard override rules (RC kill switch, ABORT forces outputs safe)
- Optional: battery low limit → reduce $u_{\max}$

### 6) Motor asymmetry
- Optional static trim: $u_L \leftarrow u_L + \delta_L$, $u_R \leftarrow u_R + \delta_R$
- Optional scaling if motors differ (later)

## Open questions
- Do ESCs support reverse? If not, how is “stop” and “turn-in-place” handled?
- Should slew-rate be applied in PWM space or normalized space?