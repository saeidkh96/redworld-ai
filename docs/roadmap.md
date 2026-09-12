# RedWorld AI Roadmap

A milestone is considered complete only when its behavior is implemented and validated.
The architecture remains modular so future domains can be added without rewriting the core.

## v0.0.1 — Foundation ✅
Project packaging, entities, Money, WorldState, SimulationEngine, API, tests, Docker, CI.

## v0.0.2 — Economic Ledger ✅
- double-entry accounts, postings and journal entries
- balanced-entry invariant
- account-type-aware balances
- immutable audit trail
- trial balance validation

## v0.0.3 — Citizens & Employment ✅
- employment contracts
- hiring state
- deterministic payroll
- citizen income and consumption accounts
- unemployment metric

## v0.0.4 — Businesses ✅
- business operating accounts
- employee-driven production
- inventory
- citizen purchases
- revenue and wage expense accounting

## v0.0.5 — Banking ✅
- bank-hosted deposit registration
- reserve-backed lending
- loan entity and credit constraint
- monthly interest accrual and scheduled principal calculation
- principal repayment lifecycle
- bank balance-sheet summary
- bank reserve movements

## v0.0.6 — Government & Fiscal System ✅
- configurable income and business taxation
- treasury and tax revenue accounts
- welfare/public spending
- fiscal events

## v0.1.0 — First Closed Economy ✅
A deterministic closed economy now executes a complete tick:

1. businesses produce
2. employers pay wages
3. government collects income tax
4. citizens consume from businesses
5. government supports unemployed citizens
6. economic aggregates refresh
7. the audit/event history records the world transition

The genesis world contains citizens, one business, one bank, one government and seeded
monetary balances. The accounting ledger remains balanced across simulation ticks.

## Next major line — v0.2.x
World expansion and autonomous behavior: needs, goals, decisions, social interactions,
agent memory, richer businesses, markets, housing, geography and institutions. New domains
must integrate through stable contracts/events rather than modifying unrelated domain logic.
