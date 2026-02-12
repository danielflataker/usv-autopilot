# Record formats (V1) — binary time series

Purpose: define the binary record layout used in `timeseries.bin`.

Design goals:
- append-only
- efficient writes (aligned, small headers)
- self-describing enough to parse with a schema version

## File structure (proposal)
1) File header (written once)
- magic bytes (e.g. "USVLOG")
- `schema_version`
- endianness (assume little-endian on STM32, but store it anyway)
- session start `t_us` (optional)
- reserved bytes for future

2) Record stream (repeated)
Each record:
- `t_us` (uint64)
- `type` (uint16)
- `len` (uint16) payload length in bytes
- `payload` (packed struct bytes, `len` long)
- optional CRC (likely not needed on SD; consider later)

This is a simple TLV-style format: easy to extend, easy to skip unknown types.

## Space efficiency and grouping
Records are *not* a single fixed-width row. Each record type has its own payload layout.
This keeps the file compact (no unused bytes for fields that don’t apply).

To reduce overhead, values that are typically plotted together are packed into the same record
(e.g. `REC_NAV_SOLUTION` contains `x,y,psi,v,r,b_g`).

## Initial record types (V1)
Pick a small set that supports EKF + LOS + PID tuning:

- `REC_NAV_SOLUTION`
  - `x, y, psi, v, r, b_g` (float32/float64 TBD)

- `REC_GUIDANCE_REF`
  - `psi_d, v_d`, optional `e_y, e_psi`

- `REC_ACTUATOR_CMD`
  - `u_s, u_d`

- `REC_ESC_OUTPUT`
  - `u_L, u_R`

Optional (depending on needs):
- `REC_SENSOR_GNSS` (raw)
- `REC_SENSOR_GYRO` (raw)

## Types and units
- `t_us`: monotonic microseconds
- SI units (m, rad, m/s, rad/s)
- angle wrapping convention referenced from `architecture.md`

## TODO / Open questions
- float precision: float32 vs float64 (V1 likely float32 for size)
- Do we want fixed-size records (fastest) or TLV (most flexible)? TLV recommended for V1.
- Versioning strategy when payload structs change
- Python parser location + minimal API (`read_timeseries.bin` → pandas)
