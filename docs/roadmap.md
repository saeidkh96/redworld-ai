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

## v1.2.0 — Human Development ✅
- skill/education growth tied to discipline and employment
- resilience-aware stress and health feedback
- long-horizon experience accumulation

## v1.3.0 — Community & Culture ✅
- persistent community groups
- belonging-driven cohesion and influence
- shared social norms and compliance dynamics

## v1.4.0 — Civic Institutions ✅
- civic council, public forum, learning commons and neighborhood assembly
- institutional trust, participation and legitimacy
- citizen civic trust feeding institutional dynamics

## v1.5.0 — Collective Behavior ✅
- public mood and social cohesion
- civic participation, polarization and collective agency
- autonomous norm reinforcement and community influence

## v2.0.0 scope — Autonomous Society ✅
The Autonomous Society capability line is integrated into the v1.1.0 release package. Society-level state now emerges deterministically from citizen life: institutions evolve, norms strengthen or weaken, community groups develop cohesion and influence, public mood and trust move with citizen well-being, and sufficiently participatory societies can produce collective decisions without direct scripted intervention.

The world remains authoritative: collective behavior can produce events and proposals, but no autonomous actor bypasses world-owned validation or the accounting/geography invariants.
