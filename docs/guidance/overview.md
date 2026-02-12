# Guidance overview (V1)

Guidance turns a mission (waypoints + segment speeds) into references for control:
- desired heading $\psi_d$
- desired speed $v_d$

It sits between estimation and control:
- consumes $(x,y,\psi)$ from the estimator
- outputs references used by the controllers

Frame conventions: see [architecture.md](../architecture.md).

## Files
- Mission / segment selection: [mission_manager.md](mission_manager.md)
- LOS guidance (heading reference): [los_guidance.md](los_guidance.md)
- Speed scheduling (caps + ramp): [speed_scheduler.md](speed_scheduler.md)

## V1 pipeline (short)
1) Mission manager selects the active segment and provides $(x_0,y_0)\rightarrow(x_1,y_1)$ and $v_{\mathrm{seg}}$
2) LOS guidance computes $\psi_d$ (and errors like $e_\psi$)
3) Speed scheduler produces $v_d$ (after caps + ramp)

## TODO / Open questions
- Do we support “stop/loiter” at final waypoint in V1, or just mark mission done?
- Should lookahead $L$ be constant in V1, or depend on speed later?