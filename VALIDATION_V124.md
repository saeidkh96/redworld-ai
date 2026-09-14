# RedWorld AI v1.2.4 Validation

## Static validation

Validated commands:

- `ruff check .`
- `mypy src`
- `pytest -q`
- `node --check src/redworld/web/app.js`
- `git diff --check`

Validated result:

- Ruff: clean
- mypy: no issues in 83 source files
- pytest: 51 tests passed
- JavaScript syntax: valid
- git diff check: no errors

Existing Starlette/httpx and anyio deprecation warnings are non-blocking and are
not introduced by v1.2.4.

## Viewer validation

Manual runtime validation confirmed:

- Genesis City map loads correctly
- live mode works
- pause/resume works
- cinematic mode works
- citizen movement is smoother
- zoom and pan are smoother
- static city geometry is no longer rebuilt on every live minute update
- frontend text encoding is clean
- the WebSocket metric is labeled `WS age`

## Scale preserved

- 1,500 citizens
- 40 businesses
- 4 civic institutions
- 1,544 autonomous agents
