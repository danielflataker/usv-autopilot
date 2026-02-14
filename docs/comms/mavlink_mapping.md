# MAVLink Mapping (V1 practical)

This page picks a *minimal* MAVLink mapping so dummy telemetry and real telemetry can share one message model.

## Use predefined MAVLink messages

- `HEARTBEAT` -> `HEARTBEAT`
- `STATUS` -> `SYS_STATUS`
- `EKF status` -> `ESTIMATOR_STATUS`
- `POSE` (local x/y + velocity) -> `LOCAL_POSITION_NED`
- `POSE` (heading/yaw-rate) -> `ATTITUDE`
- `EVENT` (human-readable) -> `STATUSTEXT`
- `PARAM_ACK` -> `PARAM_EXT_ACK`

These are supported by common GCS tooling and keep V1 simple.

## Keep custom messages for structured debug

- `USV_EVENT` for structured event payloads (machine-readable full fields)
- `USV_CTRL_DEBUG` for control internals (`v_d`, `u_s_req`, `u_d_req`, `u_s_cmd`, `u_d_cmd`, errors)
- `USV_MIXER_FEEDBACK` for saturation/achieved actuation terms

Reason: predefined messages do not carry the full project-specific control and mixer chain cleanly.

## Notes

- Dummy and real links should share the same logical message set.
- Transport can differ (dummy serial/UDP vs real SiK), but mapping should not.
- Start with predefined set first; add custom messages only where data would otherwise be lost.
