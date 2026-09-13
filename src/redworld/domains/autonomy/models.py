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
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class CommunityGroup:
    name: str
    member_ids: set[UUID] = field(default_factory=set)
    cohesion: float = 0.50
    influence: float = 0.25
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class SocietyState:
    institutions: dict[str, Institution] = field(default_factory=dict)
    groups: dict[str, CommunityGroup] = field(default_factory=dict)
    norms: dict[str, SocialNorm] = field(default_factory=dict)
    public_mood: float = 0.55
    social_cohesion: float = 0.55
    civic_participation: float = 0.35
    institutional_trust: float = 0.55
    inequality_pressure: float = 0.20
    collective_agency: float = 0.45
    polarization: float = 0.15
    decisions_made: int = 0
