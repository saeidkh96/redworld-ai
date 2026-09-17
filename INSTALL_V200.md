# RedWorld AI v1.5.0 → v2.0.0 Integration Package

This overlay was built against the supplied v1.4.0 repository. Extract/copy its contents into the repository root and replace matching files.

Integrated milestones:
- v1.5.0 Deep Citizen Life
- v1.6.0 Organizations & Society
- v1.7.0 Expanding City
- v1.8.0 History & Emergence
- v2.0.0 Living Digital World

New API surfaces:
- GET /api/v1/world/living-digital-world
- GET /api/v1/world/timeline?limit=100

Viewer:
- Adds a World Timeline panel fed by the causal timeline API.
- Existing Citizen Inspector remains available and citizen API payloads now expose living_world_v2 life-arc data.

Safety:
- Existing Human-in-the-Loop review authority is preserved.

Validate before commit/tag:
```powershell
python -m ruff format src tests
python -m ruff check .
python -m mypy src
python -m pytest -q
node --check src\redworld\web\app.js
git diff --check
git status --short
```

Package build verification in the packaging environment:
- pytest: 77 passed
- Python compileall: passed
- Node syntax check for app.js: passed
- Ruff/mypy were not installed in the packaging environment, so run the commands above in the project venv before commit/tag.
