# Kards-Simulator

Kards Simulator (engine-first, Python 3).

## Quick start

### 1) Create venv + install

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

Dev deps (tests):

```powershell
pip install -e .[dev]
pytest
```

### 2) Run the CLI prototype

```powershell
python -m kards_sim
```

This is a minimal engine prototype with:

-   2 players, deck/hand/discard
-   2-lane board model (frontline/supportline) with 5 columns
-   Actions: play unit, play order (MVP: damage), attack, end turn

## Roadmap

The goal is a faithful KARDS rules engine. Many mechanics are intentionally stubbed or simplified in this first prototype.


## Test cmd

```bash
d 2 0; e; d 0 1; d 0 2; e; a 0 0; k 3 2;
```
