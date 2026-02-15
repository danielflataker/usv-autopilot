# Record formats (V1) — binary time series

Purpose: define the binary record layout used in `timeseries.bin`.

Design goals:
- append-only
- efficient writes (aligned, small headers)
- self-describing enough to parse safely across firmware/tool changes

## Schema version
This file uses the same *contract schema* as the rest of the project:

- Firmware defines `FW_MODEL_SCHEMA` (int) and writes it into session metadata.
- `timeseries.bin` stores the same value in its header (`fw_model_schema`).
- Tools should fail fast if dataset schema != tool schema.

See: [docs/interfaces/contracts.md](../interfaces/contracts.md) (Compatibility / schema IDs).

## File structure (proposal)

### 1) File header (written once)
- magic bytes (e.g. `"USVLOG"`)
- `fw_model_schema` (uint16/uint32) — must match `FW_MODEL_SCHEMA`
- endianness (store it; assume little-endian on STM32)
- session start `t_us` (optional)
- reserved bytes for future (pad to alignment)

Note: human-readable fields like `git_sha` + `dirty` live in `meta.json` for the session folder
(not inside this binary file), so the binary stays stable and compact.

### 2) Record stream (repeated)
Each record:
- `t_us` (uint64)
- `type` (uint16)
- `len` (uint16) payload length in bytes
- `payload` (packed struct bytes, `len` long)
- optional CRC (likely not needed on SD; consider later)

This is a TLV-style format: easy to extend, easy to skip unknown types.

## Space efficiency and grouping
Records are *not* a single fixed-width row. Each record type has its own payload layout.
This keeps the file compact (no unused bytes for fields that don't apply).

To reduce overhead, values that are typically plotted together are packed into the same record
(e.g. `REC_NAV_SOLUTION` contains `x,y,psi,v,r,b_g`).

## Initial record types (V1)
Keep the initial set small so parsing + plotting is easy:

- `REC_NAV_SOLUTION`
  - `x, y, psi, v, r, b_g` (float32/float64 TBD)

- `REC_GUIDANCE_REF`
  - `psi_d, v_d`, optional `e_y, e_psi`

- `REC_ACTUATOR_REQ`
  - `u_s_req, u_d_req, src` (request stage, i.e. $\mathbf{q}=[u_s^{req},u_d^{req}]^\top$)

- `REC_ACTUATOR_CMD`
  - `u_s_cmd, u_d_cmd` (command stage, i.e. $u_s^{cmd},u_d^{cmd}$)

- `REC_MIXER_FEEDBACK`
  - `u_s_ach, u_d_ach, sat_L, sat_R, sat_any`
  - optional: `u_s_alloc, u_d_alloc`, stage saturation flags, effective limits

- `REC_ESC_OUTPUT`
  - `u_L, u_R`

Optional (if needed for tuning/debug):
- `REC_SENSOR_GNSS` (raw)
- `REC_SENSOR_GYRO` (raw)

## Types and units
- `t_us`: monotonic microseconds
- SI units (m, rad, m/s, rad/s)
- angle wrapping + frame conventions referenced from [architecture.md](../architecture.md)

## Versioning rules (simple)
- Adding a *new* record type is backwards compatible (parsers can skip unknown `type`s).
- Changing an existing payload layout is breaking -> bump `FW_MODEL_SCHEMA`.

## TODO / Open questions
- float precision: float32 vs float64 (V1 likely float32 for size)
- record IDs: enumerate in one header (`record_types.h`) and mirror in python parser
- Python parser API currently lives in `tools/log_io/io.py` (`read_timeseries_bin()`).
- Is an optional per-record CRC needed later (probably not for SD)
