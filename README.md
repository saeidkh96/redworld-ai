# RedWorld AI

<p align="center">
  <img src="assets/branding/redworld-logo.png" alt="RedWorld AI" width="900">
</p>

<p align="center">
  <strong>SIMULATE · BUILD · DECIDE · EVOLVE</strong>
</p>

<p align="center">
  An autonomous living-world simulation platform for society, economy, institutions, and intelligent citizens.
</p>

---

## Overview

**RedWorld AI** is a deterministic, extensible simulation platform for building and studying a living virtual society.

The project combines a spatial city with citizens, households, businesses, banking, government, social relationships, physical commerce, memory, goals, and an accounting-backed economy. The world itself remains the source of truth: citizens and future AI agents can propose actions, but all actions are validated and executed by world systems.

`v1.2.2 — Autonomous Living World` adds independent agent reasoning on top of Living Civilization: bounded beliefs, self-generated goals, planning, learning, agent-to-agent interaction, emergence metrics, risk evaluation and Human-in-the-Loop review for high-impact actions.

## RedWorld AI v1.3.0

The current world supports:

- **1,500+ citizens** with individual needs, traits, schedules, locations, goals, and memories
- **World time and calendar** with deterministic simulation ticks
- **Action-driven behavior** for work, movement, eating, shopping, resting, social activity, and healthcare
- **Decision policies** that operate without requiring an LLM call for every citizen
- **Spatial geography** with districts, locations, roads, and navigation
- **Mobility and daily routines** grounded in the actual world topology
- **Households** and citizen membership
- **Social relationships** including household, neighbor, and coworker connections
- **Physical commerce** with businesses, inventory, purchases, production, and consumption
- **Employment and payroll** integrated with the economy
- **Banking, taxation, government, and welfare**
- **Double-entry accounting ledger** as the financial source of truth
- **Bounded episodic memory** for citizens
- **Goals and progress evaluation**
- **Citizen Life** with education, skills, happiness, stress, health, belonging, civic trust, reputation, autonomy and aging
- **Autonomous Society** with communities, evolving norms, institutions, public mood, cohesion, participation, polarization and collective decisions
- **Autonomous agents** for citizens, businesses and institutions with bounded beliefs, goals, plans and learning
- **Agent-to-agent interaction** and emergent world metrics
- **Risk & Safety Engine** before autonomous high-impact actions
- **Human-in-the-Loop review** with Approve / Modify / Reject controls
- **Genesis City viewer** with live world and citizen state
- **FastAPI + WebSocket APIs** for simulation and visualization
- **Seeded world generation** for reproducible experiments

## Core Principles

RedWorld is designed around a few strict rules:

1. **The world owns world state.**
2. **No domain owns the whole world.**
3. **Domains communicate through explicit contracts and events.**
4. **The ledger remains the financial source of truth.**
5. **Geography owns spatial topology.**
6. **The Simulation Engine orchestrates; domain services own domain logic.**
7. **Simulation behavior should be reproducible with seeded randomness.**
8. **Infrastructure should remain replaceable.**
9. **LLMs may propose actions, but never mutate world state directly.**
10. **AI is built on top of the world, not instead of the world.**

## Architecture

```text
Experience Layer
├── REST API
├── WebSocket API
└── Genesis City Viewer

Intelligence Layer
├── Autonomous Agents
├── Decisions & Planning
├── Goals, Beliefs & Memory
├── Risk Evaluation
└── Human-in-the-Loop Review

Society Layer
├── Households
└── Social Relationships

Living World
├── Citizens
├── Needs & Traits
├── Daily Schedules
├── Actions
├── Mobility
└── Geography

Economic World
├── Commerce
├── Businesses
├── Employment
├── Banking
├── Government
├── Economy
└── Accounting Ledger

World Core
├── Time
├── Events
├── World State
├── Simulation Engine
└── Deterministic World Factory
```

### Repository structure

```text
src/redworld/
├── api/
├── core/
├── domain/
│   └── entities/
├── domains/
│   ├── accounting/
│   ├── actions/
│   ├── banking/
│   ├── businesses/
│   ├── commerce/
│   ├── decisions/
│   ├── economy/
│   ├── employment/
│   ├── geography/
│   ├── government/
│   ├── households/
│   ├── life/
│   ├── memory/
│   ├── mobility/
│   ├── planning/
│   ├── society/
│   └── time/
├── simulation/
└── web/
```

## Simulation Model

A citizen's deterministic decision cycle follows the general pattern:

```text
Observe World
     ↓
Update Needs
     ↓
Evaluate Schedule + State
     ↓
Generate Action Proposal
     ↓
Validate Constraints
     ↓
Execute Through Domain Services
     ↓
Update World State
     ↓
Record Events + Memory
     ↓
Evaluate Goals
```

This architecture allows thousands of citizens to participate in the simulation without requiring thousands of LLM requests per tick.

Future agentic or LLM-based reasoning can plug into the proposal layer while preserving deterministic world validation.

## Genesis City

Genesis City is the first visual environment for RedWorld AI.

The 2D/isometric viewer renders the simulation's actual geography rather than using a disconnected background map. It includes districts, roads, buildings, green spaces, traffic, citizens, landmarks, and live simulation information.

The backend remains authoritative. The viewer consumes snapshots and live updates rather than owning simulation state.

## API

Useful endpoints include:

```text
GET  /api/v1/health
GET  /api/v1/world
GET  /api/v1/world/map
GET  /api/v1/world/citizens
GET  /api/v1/world/citizens/{citizen_id}
GET  /api/v1/world/society
POST /api/v1/world/step
WS   /api/v1/world/live
```

Interactive API documentation is available while the server is running through FastAPI's standard documentation endpoints.

## Quick Start

### Requirements

- Python 3.14+
- Git

### Windows / PowerShell

```powershell
py -3.14 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The execution-policy change above applies only to the current PowerShell process.

### Validate

```powershell
python -m pytest
python -m ruff check .
python -m mypy src
```

Current validated development build:

```text
41 tests passed
Ruff: All checks passed
mypy: Success — 77 source files
```

### Run

```powershell
python -m uvicorn redworld.api.main:app --reload
```

Open the viewer:

```text
http://127.0.0.1:8000/viewer
```

## Release Evolution

| Version | Milestone | Status |
|---|---|---|
| `v0.1.0` | Closed Economy | Complete |
| `v0.2.0` | Living World Foundation | Complete |
| `v0.3.0` | Living Citizens | Complete |
| `v0.4.0` | Daily Life & Mobility | Complete |
| `v0.5.0` | Housing & Households | Complete |
| `v0.6.0` | Society | Complete |
| `v0.7.0` | Physical Commerce | Complete |
| `v0.8.0` | Memory & Learning Foundation | Complete |
| `v0.9.0` | Goals & Planning Foundation | Complete |
| `v1.0.0` | Living City | Complete |
| `v1.1.0` | Citizen Life / Autonomous Society | Complete |
| `v1.2.0` | Human Development → Autonomous Society | Complete |
| `v1.2.1` | Living Civilization | Complete |
| `v1.2.2` | Autonomous Living World | Complete |
| `v1.2.3` | Performance & Runtime Optimization | Complete |
| `v1.2.4` | Real-Time Viewer & Smooth Motion | Complete |
| `v1.2.5` | Entity-Level Life Events | Complete |
| `v1.2.6` | Real Economy & Employment | Complete |
| `v1.2.7` | Government & Policy Effects | Complete |
| `v1.2.8` | Dynamic City Evolution | Complete |
| `v1.2.9` | Crisis & World Events | Complete |
| `v1.3.0` | Emergent Living World | Current |

Detailed release notes are available under `docs/releases/`.

## Autonomous Living World v1.2.2

`v1.2.2` completes the autonomous-agent capability line from Autonomous Agent Core through the final Autonomous Living World integration. Citizens, businesses and institutions now observe, form bounded beliefs, prioritize goals, plan, act, interact and learn without direct per-agent commands. High-risk actions are held for Human-in-the-Loop review before any bounded simulation effect is applied.

The core agent loop is:

`Observe → Believe → Goal → Plan → Risk Check → Act/Review → Learn → Re-plan`

See `docs/V1_2_2_AUTONOMOUS_LIVING_WORLD.md` for the complete capability map and API surface.

## Emergent Living World v1.3.0

`v1.3.0` connects civilization-level outcomes to durable world-state mutations.

The evolution layer now realizes:

- births and deaths as real Citizen entity changes
- partnerships and separations as household mutations
- hiring, layoffs, business creation, and business closure
- government policy effects on real economic parameters
- city development as new geography locations
- crises as material effects on citizens and businesses
- migration as real population movement
- deterministic and idempotent monthly/yearly evolution boundaries

The evolution state is available through `GET /api/v1/world/evolution`.

## Living Civilization v1.2.1

`v1.2.1` consolidates the planned v1.2.1 → v1.3.0 Living Civilization capability line into one integrated release/tag. The simulation now tracks demographic transitions, careers and social mobility, dynamic macroeconomics, elections and policy, social pressure, city development, crises, causal history and adaptive civilization strategy.

The scope remains extensible: future releases can expand these systems into richer multi-city, regional and world-scale simulations without replacing the current foundations.

The architecture is intended to grow toward deeper citizen intelligence, richer families and organizations, education, healthcare, politics and institutions, media and culture, crime and public safety, resources and energy, environmental systems, migration, multiple cities, inter-city economies, and optional model-assisted reasoning behind the current deterministic agent contracts.

These are future directions rather than claims about the current implementation.

## Technology

- **Python**
- **FastAPI**
- **WebSockets**
- **Pydantic**
- **pytest**
- **Ruff**
- **mypy**
- **HTML / CSS / JavaScript Canvas**
- Modular domain architecture
- Deterministic seeded simulation
- Double-entry accounting

## Development Philosophy

RedWorld favors explicit state, deterministic behavior, domain boundaries, testable rules, observable events, and inspectable agent reasoning state.

The long-term goal is not simply to create many AI agents. It is to create a world with enough structure that intelligent agents have something meaningful to live in, interact with, and change.

## License

RedWorld AI is **source-available software**, not OSI open-source software.

Non-commercial use is permitted subject to the root `LICENSE`. Commercial use requires separate permission.

---

<p align="center">
  <strong>RedWorld AI</strong><br>
  SIMULATE · BUILD · DECIDE · EVOLVE
</p>

<p align="center">
  Created and developed by <strong>Saeid Khalilian</strong>
</p>
