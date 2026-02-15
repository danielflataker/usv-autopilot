# Data model (ground station)

Defines the internal data structures used by the ground station and UI:
- telemetry snapshot types
- event stream types
- mission format used by the planner UI

This should match the on-wire semantics in:
- [docs/comms/telemetry.md](../comms/telemetry.md)
- [docs/comms/params.md](../comms/params.md)
- [docs/comms/protocol.md](../comms/protocol.md)

## TODO / Outline
- Message type mapping (POSE/STATUS/EVENT/...)
- Units and frame conventions (mirror [architecture.md](../architecture.md))
- Mission representation (list of waypoints + per-segment speed)
