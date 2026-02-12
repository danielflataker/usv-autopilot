# Interfaces overview

This folder defines the “glue” between modules: shared types, message flows, and task boundaries.
These docs aim to make integration predictable and reduce merge pain.

## Files
- Contracts (structs + APIs): [contracts.md](contracts.md)
- Dataflow (who publishes what): [dataflow.md](dataflow.md)
- Modes (state machine + responsibilities): [modes.md](modes.md)
- RTOS tasks (threads, rates, priorities): [rtos_tasks.md](rtos_tasks.md)

## V1 goal
Agree on:
- a small set of canonical structs (see `contracts.md`)
- which module owns each decision
- where data crosses tasks (queues/mailboxes) vs stays in-process

Keep details flexible until code exists; update as implementation stabilizes.