# RedWorld AI Architecture

## Architectural style

RedWorld AI begins as a **modular monolith**.

This is deliberate:

- one deployable application keeps early development manageable;
- domain boundaries stay explicit;
- modules communicate through stable Python interfaces;
- infrastructure can evolve without rewriting the simulation core;
- modules can later be extracted into services if scale requires it.

## Core layers

### Domain

Pure business and simulation concepts.

Initial entities:

- Citizen
- Business
- Bank
- Government
- Economy

Value objects:

- Money

The domain layer should not depend on FastAPI, databases, message brokers, LLM vendors,
or UI frameworks.

### Simulation

Owns world state and deterministic progression of simulation time.

Initial responsibilities:

- create world state;
- maintain the simulation tick;
- advance the world.

Future responsibilities:

- event queue;
- schedules;
- action execution;
- economic clearing;
- policy application;
- agent lifecycle;
- deterministic replay.

### Application

Planned layer for use cases coordinating domain behavior.

Examples:

- hire citizen;
- pay salary;
- open account;
- issue loan;
- create business;
- collect tax;
- purchase goods.

### Infrastructure

Planned adapters:

- PostgreSQL
- Redis
- event streaming
- vector / memory stores
- LLM providers
- observability
- external APIs

### API

FastAPI is the first external interface.

The API must orchestrate the application, not contain economic rules.

## Extensibility principle

New capabilities should be introduced behind interfaces and domain services. No future
feature should require direct modification of unrelated modules merely to participate in
the world.

Potential future modules include:

- labor market
- firms and production
- accounting
- commercial banking
- central banking
- credit
- taxation
- welfare
- housing
- education
- healthcare
- demographics
- logistics
- contracts
- courts
- politics
- media
- social networks
- agent cognition
- memory and learning

## Finance direction

Finance is an operating system for the simulated economy, not a trading subsystem.

Important future concepts:

- household balances
- business balance sheets
- bank deposits
- lending
- interest
- credit risk
- cash flow
- payroll
- invoices
- taxes
- public spending
- budgets
- accounting ledgers
- insolvency
- capital formation

Trading is not a core objective.
