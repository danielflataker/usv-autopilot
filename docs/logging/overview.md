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
  - `meta.json` (build id, params snapshot, hw info)
  - `timeseries.bin` (high-rate binary records)
  - `events.jsonl` (or `events.bin` if we want strictly binary)

## High-rate time series (binary)
- single append-only file: `timeseries.bin`
- consists of fixed header + sequence of records (see `record_formats.md`)
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
- session start wall time (if available) + monotonic `t_us` info
- hardware identifiers (board, sensor models)
- parameter snapshot (or a hash + separate params file)

## TODO / Open questions
- One `timeseries.bin` vs multiple binary streams by category
- How to handle versioning of record layouts (record schema version)
- Buffer overflow strategy (drop policy + counters + event)
