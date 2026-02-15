# Command shaping (V1)

This module converts request-stage actuation $(u_s^{req},u_d^{req})$ into command-stage actuation $(u_s^{cmd},u_d^{cmd})$ before allocator feasibility logic.

## Scope
- Applies to both `AUTOPILOT` and `MANUAL`
- Owns request conditioning and command-envelope enforcement
- Does not own allocator policy, motor mixing, or ESC mapping

## Inputs
- `ACTUATOR_REQ -> actuator_req_t`
  - `u_s_req`, `u_d_req`, `src`
- mode-dependent shaping parameters
  - `act.shp.ap.u_s_scale`, `act.shp.ap.u_d_scale`
  - `act.shp.man.u_s_scale`, `act.shp.man.u_d_scale`
- command envelopes
  - `act.sw.u_s_min`, `act.sw.u_s_max`
  - `act.sw.u_d_max_neg`, `act.sw.u_d_max_pos`

## Outputs
- `ACTUATOR_CMD -> actuator_cmd_t`
  - `u_s_cmd`, `u_d_cmd`

## Stage definition

The command-shaping stage runs the following ordered operations:

1. Optional deadband/expo on request axes (typically used for `MANUAL` source)
2. Axis scaling
   - $\tilde u_s = k_s^{mode} u_s^{req}$
   - $\tilde u_d = k_d^{mode} u_d^{req}$
3. Command-envelope clamp
   - $u_s^{cmd} \in [u_s^{min},u_s^{max}]$
   - $u_d^{cmd} \in [-u_{d,max}^{-},u_{d,max}^{+}]$

The output of this stage is always command-stage naming: `u_s_cmd`, `u_d_cmd`.

## Responsibility split
- Command shaping owns mode feel, attenuation, and pre-allocation command limits.
- Allocator owns feasibility and priority when commands cannot be satisfied simultaneously.
- Mixer/motor stage owns $(u_L,u_R)$ mapping and motor-side constraints.

## Invariants
- `u_s_cmd` and `u_d_cmd` always satisfy command envelopes.
- Stage output naming is canonical and stable across docs/tools:
  - request: `u_*_req`
  - command: `u_*_cmd`
  - allocator (optional diagnostics): `u_*_alloc`
  - achieved: `u_*_ach`

## Logging and diagnostics
- `REC_ACTUATOR_REQ` stores request-stage values (`u_s_req`, `u_d_req`, `src`).
- `REC_ACTUATOR_CMD` stores command-stage values (`u_s_cmd`, `u_d_cmd`).
- Stage clamp status can be exported through controller debug fields (`sat_u_s`, `sat_u_d`) and optional mixer diagnostics (`sat_cmd_stage`).

## References
- Pipeline and stage contract: [actuation_command_pipeline_spec.md](actuation_command_pipeline_spec.md)
- Topic payloads: [../interfaces/contracts.md](../interfaces/contracts.md)
- Runtime dataflow: [../interfaces/dataflow.md](../interfaces/dataflow.md)
- Backend allocator/mixer: [mixer_and_limits.md](mixer_and_limits.md)
