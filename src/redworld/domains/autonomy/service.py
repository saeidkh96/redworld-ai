from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from redworld.core.events import DomainEvent
from redworld.domain.entities.citizen import Citizen
from redworld.domains.autonomy.models import (
    CivicDecision,
    CollectiveMovement,
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
        values = [profiles[str(c.id)] for c in citizens if str(c.id) in profiles]
        if not values:
            return
        def profile_mean(getter: Callable[[CitizenLifeProfile], float]) -> float:
            return sum(getter(profile) for profile in values) / len(values)

        mood = profile_mean(lambda p: p.happiness)
        belonging = profile_mean(lambda p: p.belonging)
        trust = profile_mean(lambda p: p.civic_trust)
        autonomy = profile_mean(lambda p: p.autonomy)
        education = profile_mean(lambda p: p.education)
        health = profile_mean(lambda p: (p.physical_health + p.mental_health) / 2)
        culture = profile_mean(lambda p: p.cultural_identity)
        mobility = profile_mean(lambda p: (p.education + p.skill + p.autonomy) / 3)
        stress = profile_mean(lambda p: p.stress)

        state.public_mood = clamp(0.75 * state.public_mood + 0.25 * mood)
        state.social_cohesion = clamp(0.70 * state.social_cohesion + 0.30 * belonging)
        state.institutional_trust = clamp(0.70 * state.institutional_trust + 0.30 * trust)
        state.civic_participation = clamp(
            0.65 * state.civic_participation + 0.35 * ((belonging + autonomy) / 2)
        )
        state.collective_agency = clamp(
            (state.civic_participation + state.social_cohesion + autonomy) / 3
        )
        state.polarization = clamp(0.55 * (1.0 - state.social_cohesion) + 0.45 * stress)
        state.education_index = clamp(0.75 * state.education_index + 0.25 * education)
        state.public_health = clamp(0.75 * state.public_health + 0.25 * health)
        state.cultural_vitality = clamp(0.70 * state.cultural_vitality + 0.30 * culture)
        state.social_mobility = clamp(0.70 * state.social_mobility + 0.30 * mobility)
        state.inequality_pressure = clamp(
            0.70 * state.inequality_pressure
            + 0.30 * ((1.0 - state.social_mobility + state.polarization) / 2)
        )

        for institution in state.institutions.values():
            institution.trust = clamp(0.8 * institution.trust + 0.2 * state.institutional_trust)
            institution.participation = clamp(
                0.8 * institution.participation + 0.2 * state.civic_participation
            )
            institution.legitimacy = clamp(
                (institution.trust + institution.participation + state.social_cohesion) / 3
            )
            institution.capacity = clamp(
                0.8 * institution.capacity + 0.2 * (institution.legitimacy + trust) / 2
            )
        for norm in state.norms.values():
            norm.compliance = clamp(0.6 * norm.compliance + 0.4 * state.social_cohesion)
            norm.strength = clamp(0.7 * norm.strength + 0.3 * norm.compliance)
        for group in state.groups.values():
            group.cohesion = clamp(0.7 * group.cohesion + 0.3 * state.social_cohesion)
            group.influence = clamp(0.6 * group.influence + 0.4 * state.civic_participation)
            group.cultural_identity = clamp(
                0.7 * group.cultural_identity + 0.3 * state.cultural_vitality
            )

        self._update_movements(state)
        if state.civic_participation >= 0.45 and tick % 96 == 0:
            self._collective_decision(tick, state, events)

    def _update_movements(self, state: SocietyState) -> None:
        if state.inequality_pressure < 0.42 and state.polarization < 0.42:
            for existing_movement in state.movements.values():
                existing_movement.intensity = clamp(existing_movement.intensity * 0.92)
            return
        cause = (
            "economic_fairness"
            if state.inequality_pressure >= state.polarization
            else "social_cohesion"
        )
        movement = state.movements.get(cause)
        pressure = max(state.inequality_pressure, state.polarization)
        if movement is None:
            state.movements[cause] = CollectiveMovement(
                f"Genesis {cause.replace('_', ' ').title()} Movement",
                state.civic_participation,
                pressure,
                cause,
            )
        else:
            movement.support = clamp(0.7 * movement.support + 0.3 * state.civic_participation)
            movement.intensity = clamp(0.7 * movement.intensity + 0.3 * pressure)

    def _collective_decision(self, tick: int, state: SocietyState, events: EventSink) -> None:
        state.decisions_made += 1
        title = (
            "Expand public learning and community programs"
            if state.education_index < state.public_health
            else "Strengthen public health and neighborhood support"
        )
        state.decision_history.append(
            CivicDecision(tick, title, state.civic_participation, True)
        )
        del state.decision_history[:-50]
        events.append(
            DomainEvent(
                "CollectiveDecisionMade",
                tick,
                {
                    "decision": state.decisions_made,
                    "title": title,
                    "agency": round(state.collective_agency, 3),
                },
            )
        )
