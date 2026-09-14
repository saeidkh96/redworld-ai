# RedWorld AI v1.2.2 Validation

Validated functional suite in the build workspace: **51 tests passed**.

Run from the repository root after copying into the local repository:

```powershell
ruff check .
mypy src
pytest -q
git diff --check
```

Runtime smoke test:

```powershell
python -m uvicorn redworld.api.main:app --reload
```

Then inspect:

- `http://127.0.0.1:8000/viewer`
- `http://127.0.0.1:8000/api/v1/world`
- `http://127.0.0.1:8000/api/v1/world/autonomy`
- `http://127.0.0.1:8000/api/v1/world/autonomy/agents?kind=citizen&limit=5`
- `http://127.0.0.1:8000/api/v1/world/autonomy/reviews`

Expected at tick 0:

- runtime version `1.2.2`
- 1,500 citizens
- 40 businesses
- 4 civic institutions
- 1,544 autonomous agents
- Living Civilization and Autonomous Society already initialized

After several ticks, autonomous decisions, plans, memory/learning and interactions should begin increasing without direct per-agent commands.
