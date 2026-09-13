from __future__ import annotations

from redworld.domain.entities.citizen import Citizen
from redworld.domains.society.models import Relationship, RelationshipType, SocialGraph


class SocietyService:
    def seed(self, citizens: list[Citizen], graph: SocialGraph) -> None:
        if len(citizens) < 2:
            return
        for index, citizen in enumerate(citizens):
            neighbor = citizens[(index + 1) % len(citizens)]
            graph.add(Relationship(citizen.id, neighbor.id, RelationshipType.NEIGHBOR, 0.35))
            if citizen.employer_id is not None:
                coworker = citizens[(index + 7) % len(citizens)]
                if coworker.employer_id == citizen.employer_id and coworker.id != citizen.id:
                    graph.add(
                        Relationship(citizen.id, coworker.id, RelationshipType.COWORKER, 0.45)
                    )

    def reinforce_interaction(self, *, citizen: Citizen, graph: SocialGraph) -> None:
        relationships = graph.for_citizen(citizen.id)
        if not relationships:
            return
        relationship = relationships[citizen.id.int % len(relationships)]
        relationship.strength = min(1.0, relationship.strength + 0.01)
