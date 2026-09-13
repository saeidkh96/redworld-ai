from __future__ import annotations

from typing import Protocol

from redworld.core.events import DomainEvent
from redworld.domain.entities.citizen import Citizen
from redworld.domains.autonomy.models import (
    CommunityGroup,
    Institution,
    InstitutionKind,
    SocialNorm,
    SocietyState,
)
from redworld.domains.life.progression import CitizenLifeProfile


class EventSink(Protocol):
    def append(self, event: DomainEvent) -> None: ...


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class AutonomousSocietyService:
    def bootstrap(self, state: SocietyState, citizens: list[Citizen]) -> None:
        if state.institutions:
            return

        for name, kind in (
            ("Genesis Civic Council", InstitutionKind.COUNCIL),
            ("Public Forum", InstitutionKind.MEDIA),
            ("Learning Commons", InstitutionKind.EDUCATION),
            ("Neighborhood Assembly", InstitutionKind.COMMUNITY),
        ):
            inst = Institution(name, kind)
            state.institutions[str(inst.id)] = inst

        for name in (
            "mutual_aid",
            "civic_duty",
            "fair_exchange",
            "public_care",
            "environmental_stewardship",
        ):
            state.norms[name] = SocialNorm(name)

        buckets = [
            CommunityGroup("North Community"),
            CommunityGroup("Central Community"),
            CommunityGroup("South Community"),
        ]

        for index, citizen in enumerate(citizens):
            buckets[index % len(buckets)].member_ids.add(citizen.id)

        for group in buckets:
            state.groups[str(group.id)] = group

    def daily_update(
        self,
        *,
        tick: int,
        state: SocietyState,
        citizens: list[Citizen],
        profiles: dict[str, CitizenLifeProfile],
        events: EventSink,
    ) -> None:
        if not citizens:
            return

        values = [profiles[str(c.id)] for c in citizens if str(c.id) in profiles]

        if not values:
            return

        mood = sum(p.happiness for p in values) / len(values)
        belonging = sum(p.belonging for p in values) / len(values)
        trust = sum(p.civic_trust for p in values) / len(values)
        autonomy = sum(p.autonomy for p in values) / len(values)

        state.public_mood = clamp(0.75 * state.public_mood + 0.25 * mood)
        state.social_cohesion = clamp(0.70 * state.social_cohesion + 0.30 * belonging)
        state.institutional_trust = clamp(0.70 * state.institutional_trust + 0.30 * trust)
        state.civic_participation = clamp(
            0.65 * state.civic_participation + 0.35 * ((belonging + autonomy) / 2)
        )
        state.collective_agency = clamp(
            (state.civic_participation + state.social_cohesion + autonomy) / 3
        )
        state.polarization = clamp(1.0 - state.social_cohesion)

        for institution in state.institutions.values():
            institution.trust = clamp(0.8 * institution.trust + 0.2 * state.institutional_trust)
            institution.participation = clamp(
                0.8 * institution.participation + 0.2 * state.civic_participation
            )
            institution.legitimacy = clamp(
                (institution.trust + institution.participation + state.social_cohesion) / 3
            )

        for norm in state.norms.values():
            norm.compliance = clamp(0.6 * norm.compliance + 0.4 * state.social_cohesion)
            norm.strength = clamp(0.7 * norm.strength + 0.3 * norm.compliance)

        for group in state.groups.values():
            group.cohesion = clamp(0.7 * group.cohesion + 0.3 * state.social_cohesion)
            group.influence = clamp(0.6 * group.influence + 0.4 * state.civic_participation)

        if state.civic_participation >= 0.45 and tick % 96 == 0:
            state.decisions_made += 1

            events.append(
                DomainEvent(
                    "CollectiveDecisionMade",
                    tick,
                    {
                        "decision": state.decisions_made,
                        "agency": round(
                            state.collective_agency,
                            3,
                        ),
                    },
                )
            )
