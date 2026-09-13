from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from redworld.domain.entities.citizen import Citizen


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class LifeStage(StrEnum):
    YOUTH = "youth"
    EARLY_ADULT = "early_adult"
    ADULT = "adult"
    MATURE_ADULT = "mature_adult"
    SENIOR = "senior"


@dataclass(slots=True)
class LifeEvent:
    year: int
    kind: str
    summary: str


@dataclass(slots=True)
class CitizenLifeProfile:
    education: float = 0.45
    skill: float = 0.45
    happiness: float = 0.55
    stress: float = 0.25
    physical_health: float = 0.90
    mental_health: float = 0.85
    belonging: float = 0.50
    civic_trust: float = 0.55
    culture: float = 0.40
    environmental_awareness: float = 0.45
    reputation: float = 0.50
    autonomy: float = 0.60
    life_satisfaction: float = 0.55
    experience_days: int = 0
    learning_progress: float = 0.0
    career_progress: float = 0.0
    burnout_risk: float = 0.05
    civic_engagement: float = 0.30
    cultural_identity: float = 0.45
    community_influence: float = 0.10
    life_stage: LifeStage = LifeStage.ADULT
    events: list[LifeEvent] = field(default_factory=list)


class CitizenProgressionService:
    @staticmethod
    def stage_for_age(age: int) -> LifeStage:
        if age < 25:
            return LifeStage.YOUTH
        if age < 35:
            return LifeStage.EARLY_ADULT
        if age < 50:
            return LifeStage.ADULT
        if age < 65:
            return LifeStage.MATURE_ADULT
        return LifeStage.SENIOR

    def daily_update(self, citizen: Citizen, profile: CitizenLifeProfile) -> None:
        profile.experience_days += 1
        employed = 1.0 if citizen.employed else 0.0
        social_health = 1.0 - citizen.needs.social
        physical = 1.0 - citizen.needs.health
        learning_rate = 0.0002 + 0.00035 * citizen.traits.discipline
        profile.learning_progress = clamp(profile.learning_progress + learning_rate)
        profile.skill = clamp(profile.skill + (0.0008 if citizen.employed else 0.00025))
        profile.education = clamp(profile.education + 0.00015 * citizen.traits.discipline)
        profile.career_progress = clamp(
            profile.career_progress + employed * (0.0003 + 0.0003 * profile.skill)
        )
        profile.stress = clamp(
            profile.stress
            + 0.008 * employed
            - 0.012 * social_health
            - 0.008 * citizen.traits.resilience
        )
        profile.burnout_risk = clamp(
            0.75 * profile.burnout_risk
            + 0.25 * (profile.stress * (1.0 - citizen.traits.resilience))
        )
        profile.physical_health = clamp(0.85 * profile.physical_health + 0.15 * physical)
        profile.mental_health = clamp(
            profile.mental_health
            + 0.006 * social_health
            - 0.009 * profile.stress
            - 0.004 * profile.burnout_risk
        )
        profile.belonging = clamp(profile.belonging + 0.006 * social_health)
        profile.reputation = clamp(profile.reputation + 0.001 * citizen.traits.discipline)
        profile.autonomy = clamp(
            0.55 * profile.autonomy + 0.45 * (0.35 + 0.35 * employed + 0.30 * profile.skill)
        )
        profile.civic_engagement = clamp(
            0.8 * profile.civic_engagement
            + 0.2 * ((profile.belonging + profile.civic_trust + profile.autonomy) / 3)
        )
        profile.cultural_identity = clamp(
            0.85 * profile.cultural_identity + 0.15 * ((profile.culture + profile.belonging) / 2)
        )
        profile.community_influence = clamp(
            (profile.reputation + profile.civic_engagement + profile.belonging) / 3
        )
        profile.happiness = clamp(
            0.28 * physical
            + 0.22 * profile.mental_health
            + 0.20 * profile.belonging
            + 0.15 * profile.autonomy
            + 0.15 * (1.0 - profile.stress)
        )
        profile.life_satisfaction = clamp(
            0.65 * profile.life_satisfaction + 0.35 * profile.happiness
        )

    def yearly_update(
        self, citizen: Citizen, profile: CitizenLifeProfile, *, year: int | None = None
    ) -> None:
        old_stage = profile.life_stage
        citizen.age += 1
        profile.life_stage = self.stage_for_age(citizen.age)
        profile.physical_health = clamp(
            profile.physical_health - max(0, citizen.age - 55) * 0.0005
        )
        profile.skill = clamp(profile.skill - max(0, citizen.age - 70) * 0.0004)
        event_year = year if year is not None else citizen.age
        if profile.life_stage != old_stage:
            profile.events.append(
                LifeEvent(event_year, "life_stage", f"Entered {profile.life_stage.value} stage")
            )
        if profile.career_progress >= 0.65 and citizen.employed:
            profile.events.append(
                LifeEvent(event_year, "career", "Reached an advanced career milestone")
            )
        if profile.burnout_risk >= 0.65:
            profile.events.append(LifeEvent(event_year, "health", "Experienced high burnout risk"))
        del profile.events[:-20]
