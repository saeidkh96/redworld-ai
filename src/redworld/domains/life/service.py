from __future__ import annotations

from redworld.domain.entities.citizen import Citizen


class LifeService:
    """Updates biological/social needs using lightweight deterministic rules."""

    def advance_needs(self, citizen: Citizen, *, minute_of_day: int) -> None:
        sleeping = citizen.current_action == "sleep"
        if sleeping:
            citizen.needs.energy -= 0.040
            citizen.needs.hunger += 0.006
            citizen.needs.social += 0.001
        else:
            citizen.needs.hunger += 0.010
            citizen.needs.energy += 0.006
            citizen.needs.social += 0.003

        if citizen.needs.hunger > 0.88:
            citizen.needs.health += 0.004
        elif citizen.needs.health > 0.03:
            citizen.needs.health -= 0.001 * citizen.traits.resilience

        if 0 <= minute_of_day < 5 * 60 and not sleeping:
            citizen.needs.energy += 0.004
        citizen.needs.clamp()

    def satisfy_food(self, citizen: Citizen) -> None:
        citizen.needs.hunger -= 0.65
        citizen.needs.health -= 0.01
        citizen.needs.clamp()

    def satisfy_sleep(self, citizen: Citizen) -> None:
        citizen.needs.energy -= 0.25
        citizen.needs.clamp()

    def satisfy_social(self, citizen: Citizen) -> None:
        citizen.needs.social -= 0.45
        citizen.needs.clamp()

    def receive_healthcare(self, citizen: Citizen) -> None:
        citizen.needs.health -= 0.55
        citizen.needs.clamp()
