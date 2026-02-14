# usv-sim

Reusable simulation helpers for the USV autopilot.

## Install

From repo root:

```bash
pip install -e ./tools/usv_sim
```

## Digital twin API (V1)

- `usv_sim.digital_twin.process_model.ProcessParams`
- `usv_sim.digital_twin.process_model.process_step()`
- `usv_sim.digital_twin.simulate.simulate()`
- `usv_sim.digital_twin.simulate.simulate_with_inputs()`
- `usv_sim.digital_twin.estimation.ExtendedKalmanFilter`
- `usv_sim.digital_twin.estimation.predict_step()`
- `usv_sim.digital_twin.current.FW_MODEL_ID`
- `usv_sim.digital_twin.current.FW_MODEL_SCHEMA`
