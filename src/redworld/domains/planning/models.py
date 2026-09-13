from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4


class GoalType(StrEnum):
    FINANCIAL_STABILITY = "financial_stability"
    HEALTH = "health"
    SOCIAL_CONNECTION = "social_connection"
    CAREER = "career"


@dataclass(slots=True)
class Goal:
    citizen_id: UUID
    goal_type: GoalType
    progress: float = 0.0
    active: bool = True
    id: UUID = field(default_factory=uuid4)
