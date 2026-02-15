# ADR 0001 — Docs and planning

## State
In use

## Why this exists
Design notes and implementation details tend to end up scattered. Key decisions can get lost, and it becomes hard to tell what's current. A lightweight workflow is needed so the project stays searchable, consistent, and easy to extend later.

## Approach

### 1) Keep documentation in the repo (`/docs`)
- `/docs` is the main place for architecture, module contracts, and protocols.
- Markdown is used so changes can be reviewed like code.
- If something matters long-term, it gets written down here.

### 2) Track work in GitHub Issues + Projects
- Issues are used for concrete tasks with a clear “done” definition.
- Projects gives a simple board (Backlog → Ready → In progress → Review → Done).
- Milestones group work (e.g. bring-up, EKF+LOS, mission upload/UI).

### 3) Use ADRs for decisions
- When a choice affects the architecture or workflow, capture it in an ADR.
- Short notes are enough: what was chosen, why, and what it changes.

### 4) Tie logs to an exact firmware build
- Firmware includes a short `git commit hash` and a `dirty` flag.
- Each SD log session writes this into `meta.json`.
- Tags can still be used for bigger milestones, but the commit hash is what matters for traceability.

### 5) CubeMX/CubeIDE generated code rules (once firmware work starts)
- Generated code stays in `/Core` and is only edited inside `USER CODE` blocks.
- Project code lives under `/App/...` to avoid being overwritten.
- `.ioc` changes are kept controlled to reduce merge conflicts.

## What this changes
- Anyone can get an overview quickly by reading `docs/index.md` and `docs/architecture.md`.
- Changes to structure and workflow are visible in the repo history.
- Logs can always be traced back to the exact code that produced them.
- Planning stays close to the code via issues and PR links.