# RedWorld AI

```{=html}
<p align="center">
```
`<img src="assets/branding/redworld-logo.png" alt="RedWorld AI" width="900">`{=html}
```{=html}
</p>
```
```{=html}
<p align="center">
```
`<strong>`{=html}SIMULATE → DECIDE → INTERACT → EVOLVE`</strong>`{=html}
```{=html}
</p>
```
```{=html}
<p align="center">
```
An autonomous living-world simulation platform for society, economy,
institutions, and intelligent citizens.
```{=html}
</p>
```

------------------------------------------------------------------------

## Overview

**RedWorld AI** is a deterministic, extensible simulation platform for
building and studying a living virtual society.

The project combines a spatial city with citizens, households,
businesses, banking, government, social relationships, physical
commerce, memory, goals, and an accounting-backed economy. The world
itself remains the source of truth: citizens and future AI agents can
propose actions, but all actions are validated and executed by world
systems.

`v2.0.0 — Living Digital World` extends the autonomous society into a
deeper, long-running digital world. Citizen life arcs, persistent
organizations, controlled urban expansion, causal history, and emergent
world events now evolve alongside the existing society and economy.
High-risk autonomous actions remain protected by Human-in-the-Loop
review.

## RedWorld AI v2.0.0

The current world supports:

-   **1,500+ citizens** with individual needs, traits, schedules,
    locations, goals, and memories
-   **World time and calendar** with deterministic simulation ticks
-   **Action-driven behavior** for work, movement, eating, shopping,
    resting, social activity, and healthcare
-   **Decision policies** that operate without requiring an LLM call for
    every citizen
-   **Spatial geography** with districts, locations, roads, and
    navigation
-   **Mobility and daily routines** grounded in the actual world
    topology
-   **Households** and citizen membership
-   **Social relationships** including household, neighbor, and coworker
    connections
-   **Physical commerce** with businesses, inventory, purchases,
    production, and consumption
-   **Employment and payroll** integrated with the economy
-   **Banking, taxation, government, and welfare**
-   **Double-entry accounting ledger** as the financial source of truth
-   **Bounded episodic memory** for citizens
-   **Goals and progress evaluation**
-   **Citizen Life** with education, skills, happiness, stress, health,
    belonging, civic trust, reputation, autonomy and aging
-   **Autonomous Society** with communities, evolving norms,
    institutions, public mood, cohesion, participation, polarization and
    collective decisions
-   **Autonomous agents** for citizens, businesses and institutions with
    bounded beliefs, goals, plans and learning
-   **Agent-to-agent interaction** and emergent world metrics
-   **Risk & Safety Engine** before autonomous high-impact actions
-   **Human-in-the-Loop review** with Approve / Modify / Reject controls
-   **Genesis City viewer** with live world and citizen state
-   **FastAPI + WebSocket APIs** for simulation and visualization
-   **Seeded world generation** for reproducible experiments
-   **Self-Evolving Civilization** with citizen minds, social ties,
    market signals, institutional feedback, generational state, causal
    records, emergent events, and adaptation
-   **Citizen intelligence → autonomous goals** integration
-   **Social dynamics → live social graph** integration
-   **Market signals → real business state** integration
-   **Urban pressure → real geography** integration
-   **Generational knowledge → citizen life profiles** integration
-   **Emergent events and adaptation → observable world mutations**
-   **Deep Citizen Life** with persistent life arcs and family,
    education, and career transitions
-   **Persistent Organizations** with business, institution, and
    community profiles plus collective behavior
-   **Controlled City Expansion** driven by world pressure and bounded
    growth
-   **Living World History** with causal timeline records for citizen,
    organization, city, crisis, and continuity events
-   **Long-running world evolution** designed for deterministic
    multi-cycle simulation
-   **Living Digital World API + timeline viewer** for inspecting the
    evolving world

## Core Principles

RedWorld is designed around a few strict rules:

1.  **The world owns world state.**
2.  **No domain owns the whole world.**
3.  **Domains communicate through explicit contracts and events.**
4.  **The ledger remains the financial source of truth.**
5.  **Geography owns spatial topology.**
6.  **The Simulation Engine orchestrates; domain services own domain
    logic.**
7.  **Simulation behavior should be reproducible with seeded
    randomness.**
8.  **Infrastructure should remain replaceable.**
9.  **LLMs may propose actions, but never mutate world state directly.**
10. **AI is built on top of the world, not instead of the world.**

## Architecture

``` text
Experience Layer
├── REST API
├── WebSocket API
└── Genesis City Viewer

Intelligence Layer
├── Autonomous Agents
├── Citizen Minds
├── Decisions & Planning
├── Goals, Beliefs & Memory
├── Risk Evaluation
└── Human-in-the-Loop Review

Living Digital World
├── Deep Citizen Life
├── Persistent Organizations
├── Controlled City Expansion
├── Causal World Timeline
└── Long-Run Evolution

Self-Evolving Civilization
├── Social Dynamics
├── Market Signals
├── Institutional Feedback
├── Generational Knowledge
├── Causal History
├── Emergent Events
└── Adaptation

Society Layer
├── Households
├── Social Relationships
├── Communities
└── Institutions

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

``` text
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
│   ├── living_world_v2/
│   ├── memory/
│   ├── mobility/
│   ├── planning/
│   ├── self_evolving/
│   ├── society/
│   └── time/
├── simulation/
└── web/
```

## Simulation Model

A citizen's deterministic decision cycle follows the general pattern:

``` text
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

This architecture allows thousands of citizens to participate in the
simulation without requiring thousands of LLM requests per tick.

Future agentic or LLM-based reasoning can plug into the proposal layer
while preserving deterministic world validation.

## Genesis City

Genesis City is the first visual environment for RedWorld AI.

The 2D/isometric viewer renders the simulation's actual geography rather
than using a disconnected background map. It includes districts, roads,
buildings, green spaces, traffic, citizens, landmarks, and live
simulation information.

The backend remains authoritative. The viewer consumes snapshots and
live updates rather than owning simulation state.

## API

Useful endpoints include:

``` text
GET  /api/v1/health
GET  /api/v1/world
GET  /api/v1/world/map
GET  /api/v1/world/citizens
GET  /api/v1/world/citizens/{citizen_id}
GET  /api/v1/world/society
GET  /api/v1/world/autonomy
GET  /api/v1/world/history
GET  /api/v1/world/events
GET  /api/v1/world/evolution
GET  /api/v1/world/self-evolving
GET  /api/v1/world/living-digital-world
GET  /api/v1/world/timeline?limit=100
POST /api/v1/world/step
WS   /api/v1/world/live
```

Interactive API documentation is available while the server is running
through FastAPI's standard documentation endpoints.

## Quick Start

### Requirements

-   Python 3.14+
-   Git

### Windows / PowerShell

``` powershell
py -3.14 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The execution-policy change above applies only to the current PowerShell
process.

### Validate

``` powershell
python -m pytest
python -m ruff check .
python -m mypy src
```

Current validated development build:

``` text
77 tests passed
Ruff: All checks passed
mypy: Success — 92 source files
JavaScript syntax validation: passed
Full simulated-year stability test: passed (35,040 ticks)
```

### Run

``` powershell
python -m uvicorn redworld.api.main:app --reload
```

Open the viewer:

``` text
http://127.0.0.1:8000/viewer
```

## Release Evolution

  Version    Milestone                                Status
  ---------- ---------------------------------------- ----------
  `v0.1.0`   Closed Economy                           Complete
  `v0.2.0`   Living World Foundation                  Complete
  `v0.3.0`   Living Citizens                          Complete
  `v0.4.0`   Daily Life & Mobility                    Complete
  `v0.5.0`   Housing & Households                     Complete
  `v0.6.0`   Society                                  Complete
  `v0.7.0`   Physical Commerce                        Complete
  `v0.8.0`   Memory & Learning Foundation             Complete
  `v0.9.0`   Goals & Planning Foundation              Complete
  `v1.0.0`   Living City                              Complete
  `v1.1.0`   Citizen Life / Autonomous Society        Complete
  `v1.2.0`   Human Development → Autonomous Society   Complete
  `v1.2.1`   Living Civilization                      Complete
  `v1.2.2`   Autonomous Living World                  Complete
  `v1.2.3`   Performance & Runtime Optimization       Complete
  `v1.2.4`   Real-Time Viewer & Smooth Motion         Complete
  `v1.3.0`   Emergent Living World                    Complete
  `v1.4.0`   Self-Evolving Civilization               Complete
  `v2.0.0`   Living Digital World                     Current

Detailed release notes are available under `docs/releases/`.

## Living Digital World v2.0.0

`v2.0.0` is the current stable milestone of RedWorld AI. It integrates
deeper citizen life, persistent organizations, controlled city growth,
historical continuity, and long-running world evolution into the
existing autonomous society and economy.

A full simulated-year validation completed successfully:

-   **35,040 simulation ticks**
-   Population: **1,500 → 1,558**
-   Businesses: **40 → 52**
-   Organizations: **47 → 59**
-   Family transitions: **16**
-   Education transitions: **34**
-   Career transitions: **803**
-   Collective organizational actions: **113**
-   Controlled city expansions: **13**
-   Historical records: **130**
-   Emergent crises: **1**
-   Human-in-the-Loop authority preserved

The v2 world state is available through
`GET /api/v1/world/living-digital-world`, while causal world history is
available through `GET /api/v1/world/timeline?limit=100`.

## Autonomous Living World v1.2.2

`v1.2.2` completes the autonomous-agent capability line from Autonomous
Agent Core through the final Autonomous Living World integration.
Citizens, businesses and institutions now observe, form bounded beliefs,
prioritize goals, plan, act, interact and learn without direct per-agent
commands. High-risk actions are held for Human-in-the-Loop review before
any bounded simulation effect is applied.

The core agent loop is:

`Observe → Believe → Goal → Plan → Risk Check → Act/Review → Learn → Re-plan`

See `docs/V1_2_2_AUTONOMOUS_LIVING_WORLD.md` for the complete capability
map and API surface.

## Self-Evolving Civilization v1.4.0

`v1.4.0` closes the v1.3.1 → v1.3.9 capability line by connecting
self-evolving civilization state to the live RedWorld domains rather
than keeping it as an isolated metrics layer.

The integrated feedback loop is:

`Agents → Decisions → Interactions → World Changes → Consequences → New Conditions → New Decisions → History`

The release includes:

-   citizen minds that influence autonomous-agent goals
-   social ties integrated with the live social graph
-   market signals that affect real business state
-   institutional feedback connected to society state
-   urban pressure that can create real geography changes
-   generational knowledge connected to citizen life profiles
-   causal records for tracing world changes
-   condition-driven emergent events with observable effects
-   adaptation feedback that changes the living world
-   preserved Human-in-the-Loop authority for high-risk autonomous
    actions

The self-evolving state is available through
`GET /api/v1/world/self-evolving`.

## Emergent Living World v1.3.0

`v1.3.0` connects civilization-level outcomes to durable world-state
mutations.

The evolution layer now realizes:

-   births and deaths as real Citizen entity changes
-   partnerships and separations as household mutations
-   hiring, layoffs, business creation, and business closure
-   government policy effects on real economic parameters
-   city development as new geography locations
-   crises as material effects on citizens and businesses
-   migration as real population movement
-   deterministic and idempotent monthly/yearly evolution boundaries

The evolution state is available through `GET /api/v1/world/evolution`.

## Living Civilization v1.2.1

`v1.2.1` established the Living Civilization layer that later releases
expanded through autonomous agents, world evolution, and self-evolving
civilization feedback. The simulation now tracks demographic
transitions, careers and social mobility, dynamic macroeconomics,
elections and policy, social pressure, city development, crises, causal
history and adaptive civilization strategy.

The scope remains extensible: post-v2 releases can expand these systems
into richer multi-city, regional and world-scale simulations without
replacing the current foundations.

The architecture is intended to continue growing toward richer families
and organizations, deeper education and healthcare systems, media and
culture, public safety, resources and energy, environmental systems,
multiple cities, inter-city economies, and optional model-assisted
reasoning behind the deterministic agent contracts.

These are future directions rather than claims about the current
implementation.

## Technology

-   **Python**
-   **FastAPI**
-   **WebSockets**
-   **Pydantic**
-   **pytest**
-   **Ruff**
-   **mypy**
-   **HTML / CSS / JavaScript Canvas**
-   Modular domain architecture
-   Deterministic seeded simulation
-   Double-entry accounting

## Development Philosophy

RedWorld favors explicit state, deterministic behavior, domain
boundaries, testable rules, observable events, and inspectable agent
reasoning state.

The long-term goal is not simply to create many AI agents. It is to
create a world with enough structure that intelligent agents have
something meaningful to live in, interact with, and change.

## License

RedWorld AI is **source-available software**, not OSI open-source
software.

Non-commercial use is permitted subject to the root `LICENSE`.
Commercial use requires separate permission.

------------------------------------------------------------------------

```{=html}
<p align="center">
```
`<strong>`{=html}RedWorld AI`</strong>`{=html}`<br>`{=html} SIMULATE →
DECIDE → INTERACT → EVOLVE
```{=html}
</p>
```
```{=html}
<p align="center">
```
Created and developed by `<strong>`{=html}Saeid
Khalilian`</strong>`{=html}
```{=html}
</p>
```
