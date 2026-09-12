# RedWorld AI v0.1.0 Validation Record

Validated in the build environment:

- Python compileall: PASS
- pytest: 17 passed
- deterministic 50-tick closed-economy run: PASS
- double-entry trial balance after 50 ticks: 0.00 RWC

The build environment did not contain Ruff or mypy binaries, so those checks are intentionally
left for the project development environment. Run `./VALIDATE_V010.ps1` from PowerShell after
installing `.[dev]`; it executes pytest, Ruff, mypy and the 50-tick invariant check.
