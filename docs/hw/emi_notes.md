# EMI / noise notes (V1)

Purpose: collect lessons and rules-of-thumb for reducing electrical noise and preventing resets/sensor glitches.

## Intended contents
- Typical noise sources (ESCs, motor leads, switching regulators, radio)
- Cable routing rules (separate power from sensor lines, twist pairs, keep loops small)
- Grounding/shielding notes (when to shield, where to terminate)
- Symptoms to watch for (GNSS dropouts, IMU spikes, MCU brownouts)

## Open questions
- Is additional filtering beyond regulators needed (LC, ferrites)?
- Where to place ferrite beads / chokes (motor leads vs sensor rails)
- How to test for EMI issues on the bench (simple procedures)
