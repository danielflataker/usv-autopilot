# Wiring and power (V1)

Purpose: describe how power is distributed and how electronics are physically wired.

This is not a final wiring diagram yet. The goal is to capture constraints and a sane plan.

## Intended contents
- Power rails (battery, 5V, 3V3), where regulation happens
- Grounding strategy (single-point vs distributed)
- Connectors and cable types (signal vs power)
- Where filtering/decoupling is placed (rail bulk caps, local caps)
- Notes on the existing “power module” and how/if it can be reused

## Open questions
- What loads need 5V vs 3V3 (final parts list needed)
- Current budget and regulator sizing
- How to keep ESC/motor noise out of sensors and MCU