# RedWorld AI v1.2.3 — Performance & Runtime Optimization

Version `1.2.3` improves the execution performance of the existing Autonomous Living World without reducing world scale or simulation capabilities.

## Runtime scale preserved

The optimized world continues to support:

- 1,500 citizens
- 40 businesses
- 4 civic institutions
- 1,544 autonomous agents
- autonomous goals, plans, actions, memory and learning
- agent interactions
- physical movement
- commerce
- accounting
- society
- civilization systems
- risk evaluation
- Human-in-the-Loop review

## Accounting optimization

The ledger now maintains incremental debit and credit totals for each account.

Before this optimization, repeated balance queries traversed historical journal entries and postings. Economy metric refreshes therefore became progressively more expensive as the simulation accumulated transactions.

The ledger now maintains:

- per-account debit totals
- per-account credit totals
- ledger-wide debit totals
- ledger-wide credit totals

Journal entries remain preserved for auditing.

## Social graph optimization

`SocialGraph` now maintains a citizen-to-relationships index.

Relationship lookup therefore avoids scanning the complete social graph for every social interaction.

## Economy aggregation optimization

Economy metrics aggregate raw Decimal balances internally.

This avoids constructing and adding thousands of temporary Money objects every tick while preserving Money values at the world-economy boundary.

## Geography optimization

`GeographyService.shortest_path()` now caches resolved routes.

The cache:

- uses `(source, target)` route keys
- stores immutable route tuples
- returns independent list copies
- is invalidated when locations or travel edges change

This preserves existing movement semantics while avoiding repeated shortest-path computation for common city routes.

## Performance result

Representative measurements on the development environment improved from approximately:

`0.70 s/tick`

to approximately:

`0.039 s/tick`

Throughput increased from approximately:

`1.4 steps/s`

to:

`25–28 steps/s`

This is roughly an 18× runtime improvement without reducing citizen count, autonomous-agent count, or simulation behavior.
