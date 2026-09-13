from __future__ import annotations

from dataclasses import dataclass


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(slots=True)
class CitizenNeeds:
    """Normalized needs where 0.0 is satisfied and 1.0 is urgent."""

    hunger: float = 0.20
    energy: float = 0.15
    social: float = 0.25
    health: float = 0.05
    safety: float = 0.05

    def clamp(self) -> None:
        self.hunger = _clamp(self.hunger)
        self.energy = _clamp(self.energy)
        self.social = _clamp(self.social)
        self.health = _clamp(self.health)
        self.safety = _clamp(self.safety)

    @property
    def urgency(self) -> float:
        return max(self.hunger, self.energy, self.social, self.health, self.safety)


@dataclass(frozen=True, slots=True)
class CitizenTraits:
    sociability: float = 0.50
    discipline: float = 0.50
    frugality: float = 0.50
    resilience: float = 0.50


@dataclass(frozen=True, slots=True)
class DailySchedule:
    wake_minute: int = 6 * 60 + 30
    work_start_minute: int = 8 * 60
    work_end_minute: int = 16 * 60 + 30
    sleep_minute: int = 22 * 60 + 30

    def is_work_time(self, minute_of_day: int) -> bool:
        return self.work_start_minute <= minute_of_day < self.work_end_minute
