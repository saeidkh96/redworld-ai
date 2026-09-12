<p align="center">
  <img src="assets/branding/redworld-logo.png" alt="RedWorld AI" width="800">
</p>

# RedWorld AI

RedWorld AI is an autonomous AI society and economy simulation platform.

The long-term vision is a persistent virtual world populated by AI citizens, businesses,
banks, government institutions, and an evolving economy. Agents will be able to work,
earn, spend, save, borrow, create businesses, hire, produce, transact, learn, and interact
inside a governed simulation.

> Current status: `v0.0.1` foundation only. Features are considered complete only after
> they are implemented and validated by tests.

## v0.0.1 scope

This first version establishes:

- modular project structure
- typed economic domain models
- money value object
- world state container
- deterministic simulation clock
- basic world creation
- FastAPI health/world endpoints
- configuration management
- automated tests
- Docker support
- GitHub Actions CI

It intentionally does **not** claim autonomous agents, LLM reasoning, banking operations,
markets, taxation, accounting, employment, production, or learning yet.

## Architecture direction

RedWorld AI starts as a modular monolith with explicit domain boundaries. This keeps the
core understandable while allowing future modules to be extracted into services if scale
or deployment requirements justify it.

Core domains:

- Citizens
- Businesses
- Banking
- Government
- Economy
- Simulation Engine

Future capabilities should depend on stable interfaces rather than directly coupling to
implementation details.

## Quick start

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run API:

```bash
uvicorn redworld.api.main:app --reload
```

Open:

- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/api/v1/health
- World: http://127.0.0.1:8000/api/v1/world

## Versioning

RedWorld AI follows semantic versioning during development.

Current target: `v0.0.1`
