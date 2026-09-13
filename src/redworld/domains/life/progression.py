from __future__ import annotations

from dataclasses import dataclass

from redworld.domain.entities.citizen import Citizen


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


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


class CitizenProgressionService:
    def daily_update(self, citizen: Citizen, profile: CitizenLifeProfile) -> None:
        profile.experience_days += 1
        employed = 1.0 if citizen.employed else 0.0
        social_health = 1.0 - citizen.needs.social
        physical = 1.0 - citizen.needs.health
        profile.skill = clamp(profile.skill + (0.0008 if citizen.employed else 0.00025))
        profile.education = clamp(profile.education + 0.00015 * citizen.traits.discipline)
        profile.stress = clamp(profile.stress + 0.008 * employed - 0.012 * social_health - 0.008 * citizen.traits.resilience)
        profile.physical_health = clamp(0.85 * profile.physical_health + 0.15 * physical)
        profile.mental_health = clamp(profile.mental_health + 0.006 * social_health - 0.009 * profile.stress)
        profile.belonging = clamp(profile.belonging + 0.006 * social_health)
        profile.reputation = clamp(profile.reputation + 0.001 * citizen.traits.discipline)
        profile.autonomy = clamp(0.55 * profile.autonomy + 0.45 * (0.35 + 0.35 * employed + 0.30 * profile.skill))
        profile.happiness = clamp(0.28 * physical + 0.22 * profile.mental_health + 0.20 * profile.belonging + 0.15 * profile.autonomy + 0.15 * (1.0 - profile.stress))
        profile.life_satisfaction = clamp(0.65 * profile.life_satisfaction + 0.35 * profile.happiness)

    def yearly_update(self, citizen: Citizen, profile: CitizenLifeProfile) -> None:
        citizen.age += 1
        profile.physical_health = clamp(profile.physical_health - max(0, citizen.age - 55) * 0.0005)
