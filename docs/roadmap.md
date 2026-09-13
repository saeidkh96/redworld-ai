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
