# usv-autopilot

Firmware + ground station for a small USV autopilot (EKF + LOS + PID, differential thrust).

## Documentation
- [Docs index](docs/index.md)
- [Architecture](docs/architecture.md)

## Tooling (quick)
- Firmware: C/C++ on STM32 (STM32CubeIDE).  
- Ground station + analysis tools: Python (Conda env in repo root).  
- Docs: Markdown in `docs/`.  

## Python environment (Conda)

Create the environment from `environment.yml`:

### Windows (PowerShell / CMD)
```bash
conda env create -f environment.yml
conda activate usv-autopilot
```

### macOS / Linux (bash/zsh)

```bash
conda env create -f environment.yml
conda activate usv-autopilot
```

If the env already exists and `environment.yml` is updated:

```bash
conda activate usv-autopilot
conda env update -f environment.yml --prune
```

## Repo layout (high level)

- `docs/` — architecture, contracts, logging/telemetry formats, test playbooks
- `firmware/` — STM32 code (added later)
- `groundstation/` — backend + frontend (added later)
- `tools/` — reusable Python tooling (sim, log parsing, plotting)
- `analysis/` — notebooks/scripts for experiments and parameter estimation
