from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from redworld.domain.entities.citizen import Citizen
from redworld.domains.planning.models import Goal, GoalType


@dataclass(slots=True)
class PlanningService:
    goals: dict[UUID, list[Goal]] = field(default_factory=dict)

    def seed_for(self, citizen: Citizen) -> None:
        citizen_goals = [
            Goal(citizen.id, GoalType.HEALTH),
            Goal(citizen.id, GoalType.FINANCIAL_STABILITY),
            Goal(citizen.id, GoalType.SOCIAL_CONNECTION),
        ]
        if citizen.employed:
            citizen_goals.append(Goal(citizen.id, GoalType.CAREER))
        self.goals[citizen.id] = citizen_goals

    def update(self, citizen: Citizen) -> None:
        for goal in self.goals.get(citizen.id, []):
            if goal.goal_type == GoalType.HEALTH:
                goal.progress = max(0.0, min(1.0, 1.0 - citizen.needs.health))
            elif goal.goal_type == GoalType.SOCIAL_CONNECTION:
                goal.progress = max(0.0, min(1.0, 1.0 - citizen.needs.social))
            elif goal.goal_type == GoalType.CAREER:
                goal.progress = 0.65 if citizen.employed else 0.10
            elif goal.goal_type == GoalType.FINANCIAL_STABILITY:
                goal.progress = 0.55 if citizen.employed else 0.20

    def for_citizen(self, citizen_id: UUID) -> list[Goal]:
        return self.goals.get(citizen_id, [])
