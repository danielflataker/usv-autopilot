# Ground station overview

This folder describes the in-repo custom ground station used for telemetry, mission upload, and basic UI (map + plots).

V1 strategy note:
- Primary field operations should work with QGroundControl via MAVLink (see ADR 0002 and `docs/comms/qgc_integration_plan.md`).
- This custom ground station is therefore optional/non-blocking for V1, and mainly a path for project-specific visualization and tooling.

## Pieces
- Backend: [backend.md](backend.md)
- Frontend: [frontend.md](frontend.md)
- Shared data model: [data_model.md](data_model.md)
- Dev setup: [dev_setup.md](dev_setup.md)

## TODO
- Keep minimal custom GS path for diagnostics that standard GCS tools do not cover.
- Document message flow (link to `docs/comms/telemetry.md` and `docs/comms/protocol.md`).
