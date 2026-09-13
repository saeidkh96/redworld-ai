from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4


class RelationshipType(StrEnum):
    HOUSEHOLD = "household"
    FRIEND = "friend"
    COWORKER = "coworker"
    NEIGHBOR = "neighbor"


@dataclass(slots=True)
class Relationship:
    source_id: UUID
    target_id: UUID
    kind: RelationshipType
    strength: float = 0.50
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class SocialGraph:
    relationships: dict[str, Relationship] = field(default_factory=dict)

    def add(self, relationship: Relationship) -> None:
        self.relationships[str(relationship.id)] = relationship

    def for_citizen(self, citizen_id: UUID) -> list[Relationship]:
        return [
            rel
            for rel in self.relationships.values()
            if rel.source_id == citizen_id or rel.target_id == citizen_id
        ]
