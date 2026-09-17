# RedWorld AI v2.0.0 — Living Digital World

## Integrated capability line

- **v1.5.0 Deep Citizen Life** — family roles, education stages, career levels, personality depth, memory depth, and generational knowledge.
- **v1.6.0 Organizations & Society** — businesses, institutions, communities, influence, resilience, and collective action.
- **v1.7.0 Expanding City** — district housing demand, land-use pressure, infrastructure load, and real geography creation.
- **v1.8.0 History & Emergence** — causal timeline records, historically significant crises, and world consequences.
- **v2.0.0 Living Digital World** — integrated inspection API, timeline API, long-run counters, citizen profiles, live map compatibility, and HITL preservation.

## Feedback loop

`Citizens → Organizations → City → Events → Consequences → History → New Conditions`

The existing world domains remain authoritative. The v2 layer observes and coordinates them; it does not replace the ledger, geography, society, autonomous-agent safety path, or simulation engine.

## API

- `GET /api/v1/world/living-digital-world`
- `GET /api/v1/world/timeline?limit=100`
- Existing citizen inspector: `GET /api/v1/world/citizens/{citizen_id}`
- Existing live viewer: `/viewer`
