from __future__ import annotations

from redworld.domain.entities.citizen import Citizen
from redworld.domains.households.models import Household


class HouseholdService:
    def create_households(self, citizens: list[Citizen]) -> dict[str, Household]:
        households: dict[str, Household] = {}
        index = 0
        household_number = 1
        while index < len(citizens):
            size = 2 + (household_number % 3)
            group = citizens[index : index + size]
            if not group:
                break
            home = group[0].home_location_id
            if home is None:
                index += len(group)
                continue
            household = Household(home_location_id=home, member_ids=[c.id for c in group])
            households[str(household.id)] = household
            for citizen in group:
                citizen.household_id = household.id
            index += len(group)
            household_number += 1
        return households
