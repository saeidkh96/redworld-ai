# RedWorld AI Roadmap

A milestone is considered complete only when its behavior is implemented and validated. The world remains modular: no domain owns the whole simulation, the financial ledger remains the source of truth for money, geography owns spatial topology, and citizen actions are validated through world-owned services.

## Foundation line ✅
- v0.0.1 — Foundation
- v0.0.2 — Economic Ledger
- v0.0.3 — Citizens & Employment
- v0.0.4 — Businesses
- v0.0.5 — Banking
- v0.0.6 — Government & Fiscal System
- v0.1.0 — First Closed Economy
- v0.1.x — Genesis City geography, viewer, dense/green city rendering and performance passes

## v0.2.0 — Living World Foundation ✅
- calendar-aware world clock
- normalized citizen needs
- action proposals and validated action execution
- deterministic, scalable decision cadence

## v0.3.0 — Living Citizens ✅
- individual traits
- daily schedules
- deterministic decision policy
- citizen action/activity state exposed through API

## v0.4.0 — Daily Life & Mobility ✅
- action-driven movement over the real geography graph
- home/work/market/park/hospital destinations
- staggered decisions and route execution

## v0.5.0 — Housing & Households ✅
- deterministic small-household generation
- household membership on citizens
- household social ties

## v0.6.0 — Society ✅
- sparse social graph
- neighbor, coworker and household relationships
- relationship reinforcement through social activity

## v0.7.0 — Physical Economy ✅
- food market state
- inventory-backed consumption
- real ledger settlement for citizen purchases
- production/restocking cadence
- daily payroll connected to the closed-economy ledger

## v0.8.0 — Memory & Learning ✅
- bounded episodic citizen memory
- meaningful purchase/social/health memories
- bounded storage for scalability

## v0.9.0 — Goals & Planning ✅
- health, financial, social and career goals
- periodic goal-progress evaluation
- goals exposed through citizen API

## v1.0.0 — Living City ✅ (development integration)
The Genesis City runtime now integrates time, needs, decisions, actions, mobility, households, society, physical commerce, bounded memory and goals into one deterministic simulation loop for 1,500+ citizens.

### Beyond v1.0
Future lines can deepen rather than replace the foundation: LLM/agentic reasoning, culture/media/politics, education, healthcare, crime/policing, energy/resources, migration, multiple cities, environment/climate and large-scale institutional experiments.

## v1.1.0 — Citizen Life ✅
- education, skills and lifelong progression
- happiness, stress, physical/mental health and life satisfaction
- belonging, civic trust, culture and environmental awareness
- reputation, autonomy and individual agency
- deterministic daily/yearly progression and aging

## v1.2.0 — Human Development → Autonomous Society ✅
This release consolidates the previously planned v1.2–v2.0 capability line under the single `v1.2.0` tag.

- Human Development: life stages, learning, skills, career, health, burnout and life history
- Community & Culture: cultural identity, community cohesion and influence
- Civic Institutions: trust, legitimacy, participation and institutional capacity
- Collective Behavior: polarization, inequality pressure and emergent movements
- Autonomous Society: development indices, bounded civic decision history and society-level events

The world remains authoritative. Society-level autonomy changes social state through deterministic domain services and explicit events; it does not bypass world validation, geography or accounting invariants.


## v1.2.1 — Living Civilization ✅
This release consolidates the planned `v1.2.1` through `v1.3.0` capability line under the single `v1.2.1` release/tag.

- Living Civilization Foundation: shared long-horizon civilization state and deterministic integration
- Life & Generations: demographic transitions, aging-linked fertility/mortality, marriage/separation and generation tracking
- Careers & Social Mobility: promotions, job changes, layoffs/hires, wage index and social-class mobility
- Dynamic Economy: demand/supply, inflation, prices, poverty, wealth concentration, productivity and confidence
- Politics & Governance: elections, governing/opposition blocs, approval, public budgets and adaptive policy enactment
- Social Dynamics: cooperation, conflict, protest pressure, opinion diversity and norm adaptation
- City Evolution: infrastructure, housing/public-space capacity, district development and land-use change
- Events & Crises: recession, shortage, epidemic, boom and policy-shock emergence with resilience/recovery
- History & Causality: bounded historical timeline with causes, effects and significance
- World Intelligence: citizen, institution and economic adaptation with an explicit civilization strategy
- Final Integration: API, viewer summary, simulation cadence, tests and release documentation

The world remains authoritative: civilization systems observe and evolve world-owned state through deterministic services and explicit events.

## v1.2.2 — Autonomous Living World ✅

This release completes the autonomous-agent roadmap as one integrated capability line:

1. Autonomous Agent Core
2. Goals, Needs & Intentions
3. Memory & Learning
4. Independent Planning
5. Agent-to-Agent Interaction
6. Limited Knowledge & Beliefs
7. Emergent Behavior
8. Risk & Safety Engine
9. Human-in-the-Loop
10. Long-Running Autonomous World
11. Autonomous World Intelligence
12. Autonomous Living World

The central simulation loop is now `Observe → Believe → Goal → Plan → Risk Check → Act/Review → Learn → Re-plan`.
High-risk actions are blocked until a human approves, rejects or modifies them.

## v1.2.3 ? Performance & Runtime Optimization ?

This release optimizes the Autonomous Living World runtime without reducing population,
agent count, simulation capabilities, or autonomous behavior.

Completed runtime improvements:

- incremental accounting balance indexes
- constant-time account balance lookups
- indexed citizen relationship lookup
- lower-overhead economy metric aggregation
- cached geographic shortest paths
- automatic route-cache invalidation
- immutable cached routes with safe per-request copies
- preserved accounting journal and audit behavior
- preserved 1,500 citizens and 1,544 autonomous agents

Representative development benchmark:

- before: approximately 0.70 seconds per simulation tick
- after: approximately 0.039 seconds per simulation tick
- throughput: approximately 25?28 simulation steps per second
- overall improvement: approximately 18x
