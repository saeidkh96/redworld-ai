# RedWorld AI v1.4.0 integration package

This package is a complete working-tree replacement for the audited v1.4.0 integration. Extract/copy it over the repository root, preserving `.git` and `.venv`, then validate locally:

```powershell
python -m ruff format src tests
python -m ruff check .
python -m mypy src
python -m pytest -q
node --check src\redworld\web\app.js
git diff --check
git status --short
```

The v1.4.0 layer is coupled to real RedWorld state: citizen minds influence autonomous goals, social dynamics synchronize into the social graph, market signals mutate business prices/wages/productivity, institutional feedback mutates society institutions, city expansion creates geography locations, generational knowledge reaches life profiles, and emergent events/adaptation mutate world state. Existing Human-in-the-Loop review remains authoritative for high-risk autonomous actions.

Do not tag/release until local validation and runtime checks pass.
