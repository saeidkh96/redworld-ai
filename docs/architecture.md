# RedWorld AI Architecture

## Goal
RedWorld is a living society/economy simulation platform. The architecture is deliberately
modular so domains such as housing, healthcare, education, justice, geography or energy can
be added later without making the simulation engine or existing domains own their logic.

## Rules
1. No domain owns the whole world.
2. Domain behavior stays independent of FastAPI and infrastructure vendors.
3. Cross-domain facts are recorded as domain events.
4. Financial state changes flow through the double-entry ledger.
5. SimulationEngine orchestrates phases; it does not contain domain-specific models.
6. New modules should expose narrow services/contracts and tests.

## Current modules
- accounting — accounts, journal entries, ledger and audit invariants
- employment — contracts and payroll construction
- businesses — production and consumption transactions
- banking — reserve-backed loans and repayments
- government — taxation and welfare
- economy — derived world metrics
- simulation — world state, genesis factory and deterministic lifecycle
- API — read/step interface only

## Extension pattern
A future `healthcare` domain can subscribe to citizen/world state, emit events such as
`TreatmentProvided`, and post financial transactions through accounting without embedding
health rules in Citizen, Government or SimulationEngine internals.

The same pattern applies to housing, education, justice, transport, energy, climate,
politics, media and other future world systems.
