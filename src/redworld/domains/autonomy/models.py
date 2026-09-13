from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4


class InstitutionKind(StrEnum):
    COUNCIL = "council"
    COMMUNITY = "community"
    MEDIA = "media"
    EDUCATION = "education"
    CIVIC = "civic"


@dataclass(slots=True)
class SocialNorm:
    name: str
    strength: float = 0.50
    compliance: float = 0.50


@dataclass(slots=True)
class Institution:
    name: str
    kind: InstitutionKind
    trust: float = 0.55
    legitimacy: float = 0.60
    participation: float = 0.35
    capacity: float = 0.60
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class CommunityGroup:
    name: str
    member_ids: set[UUID] = field(default_factory=set)
    cohesion: float = 0.50
    influence: float = 0.25
    cultural_identity: float = 0.45
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class CollectiveMovement:
    name: str
    support: float
    intensity: float
    cause: str


@dataclass(slots=True)
class CivicDecision:
    tick: int
    title: str
    support: float
    enacted: bool


@dataclass(slots=True)
class SocietyState:
    institutions: dict[str, Institution] = field(default_factory=dict)
    groups: dict[str, CommunityGroup] = field(default_factory=dict)
    norms: dict[str, SocialNorm] = field(default_factory=dict)
    movements: dict[str, CollectiveMovement] = field(default_factory=dict)
    decision_history: list[CivicDecision] = field(default_factory=list)
    public_mood: float = 0.55
    social_cohesion: float = 0.55
    civic_participation: float = 0.35
    institutional_trust: float = 0.55
    inequality_pressure: float = 0.20
    collective_agency: float = 0.45
    polarization: float = 0.15
    cultural_vitality: float = 0.50
    public_health: float = 0.80
    education_index: float = 0.50
    social_mobility: float = 0.45
    decisions_made: int = 0
