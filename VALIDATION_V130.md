# Validation - v1.3.0

RedWorld AI v1.3.0 was validated in the project's Windows Python 3.14 virtual environment.

## Final validation

- Ruff: PASS
- mypy: PASS - 86 source files
- pytest: PASS - 63 tests
- Entity evolution tests: PASS - 12 tests
- JavaScript syntax (`node --check`): PASS
- `git diff --check`: PASS (line-ending warnings only)

## Entity-level behavior validated

The v1.3.0 evolution suite verifies:

- real citizen births and household membership
- real citizen deaths
- household partnerships and separations
- real hiring and layoffs
- real business creation
- government policy effects
- physical city/location development
- crisis effects on world entities
- positive and negative migration
- monthly mutation idempotency
- v1.3.0 evolution snapshot and version reporting

## Non-blocking warnings

The test suite reports two dependency deprecation warnings from Starlette/httpx and anyio.
They do not affect the v1.3.0 validation result.
