# Backend (ground station)

Responsibilities (V1):
- Connect to telemetry radio (serial)
- Decode frames and publish telemetry to the UI
- Send commands (mission upload, param set, start/stop)

Keep it simple and observable (logs + metrics).

## TODO / Outline
- Serial connection and reconnect behavior
- Message routing (best-effort telemetry vs reliable transactions)
- Rate limiting for UI-driven actions (params, commands)
- Logging to disk for later analysis (optional)