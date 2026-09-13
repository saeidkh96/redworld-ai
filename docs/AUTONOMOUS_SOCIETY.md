# Autonomous Society

RedWorld AI's Autonomous Society layer turns individual citizen state into persistent society-level dynamics while preserving deterministic simulation rules.

## Citizen Life
Each citizen receives a bounded life profile covering education, skill, happiness, stress, physical and mental health, belonging, civic trust, culture, environmental awareness, reputation, autonomy, life satisfaction and accumulated experience. Profiles evolve through deterministic daily progression; aging is handled on yearly boundaries.

## Communities and Norms
Citizens are organized into persistent community groups. Group cohesion and influence react to society-wide belonging and participation. Shared norms track both strength and compliance, allowing social expectations to evolve rather than remain static constants.

## Institutions
Genesis City bootstraps civic institutions representing deliberation, public information, learning and neighborhood organization. Their trust, legitimacy and participation change with citizen civic trust, cohesion and participation.

## Emergent Society Metrics
The society layer exposes public mood, social cohesion, civic participation, institutional trust, collective agency, inequality pressure and polarization. These metrics are derived from citizen state rather than randomly assigned each tick.

## Collective Decisions
When civic participation is sufficiently strong, the autonomous society can produce `CollectiveDecisionMade` domain events on a bounded cadence. This is intentionally an event/proposal boundary: the society cannot mutate protected world state, money or geography directly.

## API
`GET /api/v1/world/society` exposes institutions, groups, norms and emergent society metrics. Citizen detail responses expose the Citizen Life profile, while the world summary contains compact Autonomous Society metrics.
