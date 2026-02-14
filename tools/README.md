# tools/README.md

Reusable tooling: log parsing, decoding, plotting helpers, conversion scripts.

- Keep one-off exploration in [`analysis/`](../analysis/).
- Tools should be runnable from repo root and prefer documented CLI usage.

## Dummy log generator

Generate synthetic STM32-style session folders for parser/analysis/groundstation testing:

```bash
python tools/generate_dummy_logs.py --scenario step
python tools/generate_dummy_logs.py --scenario zigzag --duration-s 90 --dt 0.05
```

Output layout:

- `logs/YYYYMMDD_HHMMSS/meta.json`
- `logs/YYYYMMDD_HHMMSS/timeseries.bin`
- `logs/YYYYMMDD_HHMMSS/events.jsonl`

`timeseries.bin` includes process-chain records for:

- estimator state + diagnostics + raw sensor snapshots
- mission/guidance/speed scheduler
- controller command/debug
- mixer feedback + ESC output

Parse logs (dummy or real) with shared log IO:

```bash
python -c "from tools.log_io import read_timeseries_bin; d=read_timeseries_bin('logs/20260214_120000/timeseries.bin'); print(d.record_counts)"
```

Shared record layout contract lives in `tools/log_io/layout.py`.

## Dummy telemetry emitter

Replay a log session as MAVLink-aligned telemetry JSONL:

```bash
python tools/emit_dummy_telemetry.py --session-dir logs/20260214_120000 --out telemetry.jsonl
```

This emits a minimal V1 set using predefined MAVLink names (`HEARTBEAT`, `SYS_STATUS`,
`ESTIMATOR_STATUS`, `LOCAL_POSITION_NED`, `ATTITUDE`, `STATUSTEXT`, `PARAM_EXT_ACK`)
and can optionally add custom debug messages with `--include-custom`.
