# Speed scheduler (V1)

The speed scheduler turns a per-segment target speed into a smooth speed setpoint for the surge speed controller.

Key idea: many parts of the pipeline may want to *cap* the segment speed. We apply these caps first, then ramp the final target to avoid step changes into the PID.

## Symbols
- $v_{\mathrm{seg}}$: segment target speed from the mission (piecewise constant)
- $v_{\mathrm{cap}}$: capped target speed after all limiting rules (the “final target”)
- $v_d$: ramped desired speed sent to the speed controller (stateful; stored between cycles)
- $\Delta t$: control period
- $a_{\uparrow}$: max setpoint acceleration ($\mathrm{m/s^2}$)
- $a_{\downarrow}$: max setpoint deceleration ($\mathrm{m/s^2}$)
- $d_{\mathrm{wp}}$: distance to next waypoint
- $e_\psi \stackrel{\text{def}}{=} \mathrm{wrap}(\psi_d - \psi)$: heading error

## Pipeline
1) Start with mission speed:
```math
v_0 \stackrel{\text{def}}{=} v_{\mathrm{seg}}.
```

2) Apply any number of *caps* (each rule computes an upper bound $v_{\max,i}$):
```math
v_{i+1} \stackrel{\text{def}}{=} \min\!\left(v_i,\; v_{\max,i}\right).
```

After all rules:
```math
v_{\mathrm{cap}} \stackrel{\text{def}}{=} v_N.
```

3) Ramp the controller setpoint toward the capped target:
```math
\Delta v \stackrel{\text{def}}{=} \mathrm{sat}\!\left(v_{\mathrm{cap}} - v_d,\; -a_{\downarrow}\Delta t,\; a_{\uparrow}\Delta t\right),
\qquad
v_{d}^{+} \stackrel{\text{def}}{=} v_d + \Delta v.
```

Finally, output $v_d \leftarrow v_d^{+}$.

This ramp uses the previous setpoint $v_d$ (stateful) and does not require the speed estimate $\hat v$.

## V1 caps (minimal)
### A) Slow down near waypoint (optional)
Define a waypoint slow zone (example parameters):
- $d_{\mathrm{slow}}$: distance where slowdown begins
- $v_{\mathrm{wp}}$: max allowed speed inside the slow zone

Example cap:
- if $d_{\mathrm{wp}} < d_{\mathrm{slow}}$, set $v_{\max,\mathrm{wp}} = v_{\mathrm{wp}}$
- else $v_{\max,\mathrm{wp}} = +\infty$

### B) Slow down on large heading error (optional)
Define a heading error threshold and cap:
- if $|e_\psi| > e_{\psi,\mathrm{th}}$, set $v_{\max,\psi} = v_{\psi}$
- else $v_{\max,\psi} = +\infty$

## Future caps (placeholders)
These should fit the same pattern ($v \leftarrow \min(v, v_{\max})$):
- close to land / geofence
- low battery / thermal limits
- EKF unhealthy / degraded mode
- manual operator “speed limit” knob

## TODO / Open questions
- Do we enforce a minimum speed floor (to keep steering/heading observable)?
- Where should “hard” safety limits live: here or in the mode/state machine?
- How do we choose $a_{\uparrow}, a_{\downarrow}$ (direct $\mathrm{m/s^2}$ vs derived from $v_{\max}/T$)?