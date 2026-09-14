# RedWorld AI v1.2.2 — Autonomous Living World

`v1.2.2` completes the autonomous-agent capability line on top of the Living Civilization foundation.
The world no longer depends only on externally selected citizen actions. Citizens, businesses and civic institutions now maintain their own bounded state, observe the world from incomplete information, form goals, create plans, act, interact and learn from outcomes.

## Completed capability line

1. **Autonomous Agent Core** — citizens, businesses and institutions are represented as independent agents.
2. **Goals, Needs & Intentions** — citizen agents derive priorities from health, employment, social need, stress and skill.
3. **Memory & Learning** — action outcomes are stored in bounded agent memory and feed progress.
4. **Independent Planning** — agents build multi-step plans and re-plan when their highest-priority goal changes.
5. **Agent-to-Agent Interaction** — agents exchange information without a direct user command.
6. **Limited Knowledge & Beliefs** — agents reason from personal observations with confidence and deterministic perception noise rather than reading perfect global state.
7. **Emergent Behavior** — collective signal, learning and emergence metrics are calculated from independent planning, interaction and society state.
8. **Risk & Safety Engine** — autonomous intents receive a bounded risk score before execution.
9. **Human-in-the-Loop** — high-risk actions are blocked and added to a review queue. A human can approve, reject or modify the proposal before any bounded simulation effect is applied.
10. **Long-Running Autonomous World** — the existing simulation engine continuously advances autonomous agents together with economy, society, government, city and history.
11. **Autonomous World Intelligence** — agent adaptation is connected to the Living Civilization state rather than operating as an isolated demo.
12. **Autonomous Living World** — API, viewer, tests and documentation expose the integrated system.

## Autonomous loop

Each citizen agent follows a bounded deterministic cycle:

`Observe → Form beliefs → Prioritize goals → Plan → Risk check → Act or wait for review → Learn → Re-plan`

Organizations run on slower cadences so the world remains practical with 1,500 citizens.

## Human-in-the-Loop

Low- and medium-risk actions can execute autonomously. High-risk and critical actions never execute immediately. They enter `pending_reviews` with:

- actor and agent kind
- intent and reason
- risk level and score
- expected world impact
- creation tick

Review decisions are `approved`, `rejected` or `modified`. The simulator only applies bounded, abstract consequences after approval/modification.

## API

- `GET /api/v1/world/autonomy`
- `GET /api/v1/world/autonomy/agents`
- `GET /api/v1/world/autonomy/agents/{agent_id}`
- `GET /api/v1/world/autonomy/reviews`
- `POST /api/v1/world/autonomy/reviews/{review_id}?decision=approved|rejected|modified`

Citizen details now include their autonomous-agent beliefs, goals, plans and bounded learning history.

## Viewer

The Genesis City viewer adds:

- autonomous-agent count
- emergence metric
- Human-in-the-Loop pending count
- autonomous-agent details in Citizen Inspector
- a Human Review panel with Approve / Modify / Reject controls

## Design constraints

The autonomous layer stays deterministic and testable. It does not require an external LLM or hidden remote service. Future model adapters can be introduced behind the planning/decision boundary without making the world dependent on a single vendor.
