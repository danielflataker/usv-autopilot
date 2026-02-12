# Frontend (ground station)

Responsibilities (V1):
- Show boat position on a map
- Show basic status (mode, battery, EKF health)
- Simple controls: upload mission, start/stop, abort
- Minimal plots (speed, heading, cross-track)

## TODO / Outline
- Map view (local xy vs lat/lon decision)
- Plotting (downsample + time axis from $t_{us}$)
- UX rule: avoid “spammy” sliders unless rate-limited