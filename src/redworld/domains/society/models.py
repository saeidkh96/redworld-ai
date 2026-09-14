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

    _by_citizen: dict[UUID, list[Relationship]] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        """Build citizen relationship indexes for preloaded graph data."""
        for relationship in self.relationships.values():
            self._index_relationship(relationship)

    def add(self, relationship: Relationship) -> None:
        key = str(relationship.id)

        existing = self.relationships.get(key)
        if existing is not None:
            self._remove_from_index(existing)

        self.relationships[key] = relationship
        self._index_relationship(relationship)

    def _index_relationship(self, relationship: Relationship) -> None:
        self._by_citizen.setdefault(relationship.source_id, []).append(relationship)

        if relationship.target_id != relationship.source_id:
            self._by_citizen.setdefault(relationship.target_id, []).append(relationship)

    def _remove_from_index(self, relationship: Relationship) -> None:
        source_relationships = self._by_citizen.get(relationship.source_id)
        if source_relationships is not None:
            self._by_citizen[relationship.source_id] = [
                item for item in source_relationships if item.id != relationship.id
            ]
            if not self._by_citizen[relationship.source_id]:
                del self._by_citizen[relationship.source_id]

        if relationship.target_id == relationship.source_id:
            return

        target_relationships = self._by_citizen.get(relationship.target_id)
        if target_relationships is not None:
            self._by_citizen[relationship.target_id] = [
                item for item in target_relationships if item.id != relationship.id
            ]
            if not self._by_citizen[relationship.target_id]:
                del self._by_citizen[relationship.target_id]

    def for_citizen(self, citizen_id: UUID) -> list[Relationship]:
        return self._by_citizen.get(citizen_id, [])
