# RedWorld AI v1.2.1 — Living Civilization Manifest

This package consolidates the planned v1.2.1 → v1.3.0 capability line under one final release version/tag: `v1.2.1`.

## Capability map

- Living Civilization Foundation → `domains/civilization/models.py`, `service.py`, `WorldState.civilization`
- Life & Generations → demographic population, births/deaths, marriage/separation, dependency ratio, generation tracking
- Careers & Social Mobility → mobility, promotions, job changes, hires/layoffs, career ladder, wage index, social classes
- Dynamic Economy → price index, inflation, demand/supply, poverty, wealth concentration, business births/failures, confidence/productivity
- Politics & Governance → elections, political blocs, seats, approval, budget capacity, policies and effectiveness
- Social Dynamics → cooperation, conflict, protest pressure, civic campaigns, opinion diversity, norm adaptation
- City Evolution → infrastructure, housing/public-space capacity, migration balance, construction, district development and land-use changes
- Events & Crises → recession, shortage, epidemic, boom, policy shock, recovery/resilience
- History & Causality → bounded historical records with causes/effects/significance
- World Intelligence → citizen/institution/economic adaptation, foresight and adaptive civilization strategy
- Final Integration → simulation cadence, API, viewer metrics, tests and docs

## New API surfaces

- `GET /api/v1/world/civilization`
- `GET /api/v1/world/history`
- `GET /api/v1/world` now includes `living_civilization`

## Release version

- Package/runtime version: `1.2.1`
- Intended Git tag: `v1.2.1`
- No intermediate v1.2.2 ... v1.3.0 release tags are required for this consolidated build.
