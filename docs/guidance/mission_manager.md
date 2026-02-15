# Mission manager (V1)

Responsible for selecting the active waypoint segment and deciding when to switch to the next one. Guidance and speed scheduling should not care about mission storage details.

Frame conventions: see [architecture.md](../architecture.md).

## Mission representation (minimal)
A mission is an ordered list of waypoints in local coordinates:
- waypoint $i$: $(x_i, y_i)$
- optional per-segment target speed $v_{\text{seg},i}$ for segment $i \rightarrow i+1$

(Exact file format / upload protocol is defined in `docs/comms/`.)

## State
- `idx`: active segment index (from waypoint `idx` to `idx+1`)
- `active`: mission armed/active flag
- `done`: mission completed flag

## Outputs (contract)
Given current estimate $(x,y)$, provide:
- segment endpoints: $(x_i,y_i)$ and $(x_{i+1},y_{i+1})$
- distance to next waypoint: $d_{\text{wp}}$
- along-track progress: $s$ on the segment
- segment speed target: $v_{\text{seg}}$

## Waypoint switching (V1)
Basic rule:
- switch to next segment when $d_{\text{wp}} < r_{\text{acc}}$

Also implement:
- hysteresis: once switched, don't switch back unless mission is reset
- ignore switching if mission not active

## TODO / Open questions
- Should "loiter/stop" be supported at the last waypoint, or should `done` transition to IDLE?
- Are per-waypoint acceptance radii needed, or is a single global $r_{\text{acc}}$ enough in V1?
- Should a "current segment" snapshot be exposed over telemetry (useful for debugging)?
