# Logging overview

Purpose: store on-boat data for tuning and post-analysis without ever blocking the control loop.

Principles:
- control loop only appends to ringbuffers (non-blocking)
- SD writing happens in a low-priority logger task (batched)
- high-rate data is **binary**
- sparse events are stored separately

## Session layout (proposed)
On boot or “start logging”, create a new session folder:
- `logs/YYYYMMDD_HHMMSS/`
  - `meta.json` (build id, `FW_MODEL_SCHEMA`, params snapshot, hw info)
  - `timeseries.bin` (high-rate binary records)
  - `events.jsonl` (or `events.bin` if we want strictly binary)

## Schema / compatibility (must match firmware + tools)
Some contracts must match exactly (state order/meaning, units, record layouts). We use a single schema ID:

- Firmware defines `FW_MODEL_SCHEMA` and logs it in `meta.json`
- `timeseries.bin` header stores the same `fw_model_schema`
- tools should fail fast if dataset schema != tool schema

See: [`record_formats.md`](record_formats.md), [`interfaces/contracts.md`](../interfaces/contracts.md), and [`contract_sync.md`](contract_sync.md).

## High-rate time series (binary)
- single append-only file: `timeseries.bin`
- fixed header + TLV record stream (see [`record_formats.md`](record_formats.md))
- designed for fast writes and easy parsing in Python

### Why a single `timeseries.bin` is OK
We log time series as *typed binary records* (TLV): each record stores only the fields it needs.

This avoids the “wide CSV row” problem where most columns are unused most of the time.
Overhead per record is small (timestamp + type + payload length).

We only split into multiple `.bin` files if we later add a very high-rate stream (e.g. raw IMU)
that should not compete with core nav/control logs.

## Event log (separate)
- `events.jsonl` (one JSON object per line) is acceptable since it is low-rate
  - easy to read/debug
  - doesn’t bloat SD writes
- alternative: `events.bin` with fixed structs (later)

## Metadata (`meta.json`)
Should include:
- firmware build id: `git_sha` + `dirty` flag
- `FW_MODEL_SCHEMA` (contract schema id)
- session start wall time (if available) + monotonic `t_us` info
- hardware identifiers (board, sensor models)
- parameter snapshot (or a hash + separate params file)

## TODO / Open questions
- When to move from `events.jsonl` to `events.bin`
- Buffer overflow strategy (drop policy + counters + event)
- If/when to split `timeseries.bin` into multiple streams (only if needed)
