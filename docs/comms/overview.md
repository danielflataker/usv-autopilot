# Comms overview

This folder describes how the boat and ground station talk to each other: what gets sent, how it's framed, and how parameters are updated.

Keep this practical and avoid duplicating internal structs from `interfaces/`.

## What lives here
- Telemetry: messages sent from boat → ground station (status, pose, events, etc.)
- Protocol: framing, reliability, and transactions (mission upload, ACK/timeout, resync)
- Params: parameter listing + how parameters are set/apply/acked over the link

## Files
- `telemetry.md` — message types, fields, units, and recommended rates
- `protocol.md` — serial framing + ACK/retry + mission upload flow
- `params.md` — param IDs/names/types, apply rules, and logging of param changes
- `mavlink_mapping.md` — which V1 telemetry uses predefined MAVLink vs custom messages
- `telemetry_implementation_plan.md` — milestone plan and acceptance criteria for dummy -> real telemetry
- `qgc_integration_plan.md` — concrete MAVLink compatibility checklist for QGC-first operations

## References
- Internal contracts/structs: `../interfaces/contracts.md`
- Ground station implementation details: `../groundstation/overview.md`

## TODO / Outline
- Define link assumptions (SiK rate, expected packet loss, max payload)
- Decide message set for V1 (minimal telemetry + events + param ack)
- Decide protocol approach (subset of MAVLink vs custom framing)
- Prefer QGC-first compatibility path for V1 mission operations
- Define mission upload transaction (start → chunks → commit → ack)
- Define parameter update behavior (batch apply, rate limiting, safe apply rules)

## Open questions
- Is any custom framing still justified after QGC-first decision?
- How much reliability is needed for each message type (telemetry best-effort vs commands reliable)?
