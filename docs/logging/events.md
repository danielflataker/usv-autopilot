# Events (V1)

Purpose: sparse log of discrete changes and faults.
Used for slicing runs (mode switches, tests) and for debugging.

Events are separate from the high-rate binary time series.

## Format (V1 proposal)
- file: `events.jsonl` (JSON Lines)
- each line is one event object:
  - `t_us` (monotonic timestamp)
  - `type` (string or small enum name)
  - optional payload fields

Example:
- `{"t_us":12345678,"type":"MODE_CHANGE","from":"MANUAL","to":"AUTOPILOT","reason":"RC_SWITCH"}`

## Examples (V1)
- `FW_INFO`: `git_sha`, `git_dirty`
- `MODE_CHANGE`: from → to, reason
- `MISSION_START` / `MISSION_DONE`
- `WP_SWITCH`: idx, d_wp
- `PARAM_APPLY`: id, old → new
- `EKF_GATING`: sensor, metric, action
- `LINK_LOSS` / `LINK_REGAIN`
- `LOG_OVERFLOW`: dropped counts, watermarks

## Implementation notes
- Events are emitted at the source (mode manager, EKF, params, logger, …)
- Events may have multiple consumers (e.g. SD writer, live link, debug), but that wiring is described elsewhere
- If buffers overflow: drop events and increment counters (and optionally emit a summary event later)

## TODO / Open questions
- Exact event type list + required payload keys
- JSONL vs binary events (JSONL is fine for V1)
- Max event rate and buffer sizing
