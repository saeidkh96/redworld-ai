from __future__ import annotations

import hashlib
from typing import Any

from redworld.core.events import DomainEvent
from redworld.domains.geography import Coordinate, Location, LocationType

from .models import (
    CitizenArc,
    LivingDigitalWorldState,
    OrganizationProfile,
    TimelineRecord,
    UrbanDistrictState,
)


def stable(*parts: object) -> int:
    raw = "|".join(map(str, parts)).encode()
    return int(hashlib.sha256(raw).hexdigest()[:16], 16)


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class LivingDigitalWorldService:
    """v1.5-v2.0 integration layer built on authoritative RedWorld domains."""

    def bootstrap(self, world: Any) -> None:
        state: LivingDigitalWorldState = world.living_world_v2
        active = set(world.citizens)
        for citizen_id in list(state.citizen_arcs):
            if citizen_id not in active:
                del state.citizen_arcs[citizen_id]

        for citizen_id, citizen in world.citizens.items():
            arc = state.citizen_arcs.get(citizen_id)
            if arc is None:
                arc = CitizenArc(citizen_id)
                state.citizen_arcs[citizen_id] = arc

            if not arc.initialized:
                arc.family_role = self._family_role(world, citizen)
                arc.education_stage = self._education_stage(citizen.age)
                arc.career_level = self._career_level(world, citizen_id)
                arc.initialized = True

            mind = world.self_evolving.minds.get(citizen_id)
            if mind is not None:
                arc.personality_depth = clamp((mind.knowledge + mind.reputation) / 2)
                arc.legacy_knowledge = mind.knowledge
            arc.memory_depth = clamp(len(world.memories.recent(citizen.id)) / 16)

        active_orgs: set[str] = set()
        for business_id, business in world.businesses.items():
            active_orgs.add(business_id)
            org = state.organizations.get(business_id)
            if org is None:
                org = OrganizationProfile(business_id, "business")
                state.organizations[business_id] = org
            org.kind = "business"
            org.members = self._employee_count(world, business.id)
            org.influence = clamp(float(business.productivity_per_employee) / 3)
            org.resilience = 0.55

        for institution_id, institution in world.autonomous_society.institutions.items():
            active_orgs.add(institution_id)
            org = state.organizations.get(institution_id)
            if org is None:
                org = OrganizationProfile(institution_id, "institution")
                state.organizations[institution_id] = org
            org.kind = "institution"
            org.members = 0
            org.influence = clamp(institution.capacity)
            org.resilience = clamp(institution.legitimacy)

        for group_id, group in world.autonomous_society.groups.items():
            active_orgs.add(group_id)
            org = state.organizations.get(group_id)
            if org is None:
                org = OrganizationProfile(group_id, "community")
                state.organizations[group_id] = org
            org.kind = "community"
            org.members = len(group.member_ids)
            org.influence = clamp(group.influence)
            org.resilience = clamp(group.cohesion)

        for org_id in list(state.organizations):
            if org_id not in active_orgs:
                del state.organizations[org_id]

        for district_id in world.geography.districts:
            state.urban_districts.setdefault(district_id, UrbanDistrictState(district_id))

    def update(self, world: Any) -> None:
        self.bootstrap(world)
        state = world.living_world_v2
        day_key = f"{world.clock.year:04d}-{world.clock.month:02d}-{world.clock.day:02d}"
        month_key = f"{world.clock.year:04d}-{world.clock.month:02d}"
        if state.last_day != day_key:
            state.last_day = day_key
            self._daily(world)
        if state.last_month != month_key:
            state.last_month = month_key
            self._monthly(world)
        if state.last_year != world.clock.year:
            state.last_year = world.clock.year
            self._yearly(world)

    def _daily(self, world: Any) -> None:
        state = world.living_world_v2
        for citizen_id, arc in state.citizen_arcs.items():
            profile = world.life_profiles.get(citizen_id)
            if profile is None:
                continue
            arc.memory_depth = clamp(
                0.7 * arc.memory_depth + 0.3 * min(1.0, len(profile.events) / 10)
            )
            arc.personality_depth = clamp(
                0.7 * arc.personality_depth
                + 0.3 * ((profile.autonomy + profile.reputation + profile.belonging) / 3)
            )
        if world.tick:
            state.long_run_cycles += 1

    def _monthly(self, world: Any) -> None:
        state = world.living_world_v2
        population = max(1, len(world.citizens))
        candidates: list[tuple[float, int, str, UrbanDistrictState]] = []

        for district_id, district_state in state.urban_districts.items():
            locations = world.geography.district_locations(district_id)
            location_ids = {loc.id for loc in locations}
            homes = sum(1 for loc in locations if loc.location_type == LocationType.HOME)
            residents = sum(
                1 for citizen in world.citizens.values() if citizen.home_location_id in location_ids
            )
            capacity = max(1, homes * 4)
            district_state.housing_demand = clamp(residents / capacity)
            district_state.land_use_pressure = clamp(len(locations) / max(8, population / 100))
            district_state.infrastructure_load = clamp(
                (district_state.housing_demand + world.self_evolving.housing_pressure) / 2
            )
            if district_state.infrastructure_load > 0.62:
                cooldown = max(0, world.tick - district_state.last_expansion_tick)
                if district_state.last_expansion_tick < 0 or cooldown >= 5760:
                    candidates.append(
                        (
                            district_state.infrastructure_load,
                            stable(
                                world.clock.year,
                                world.clock.month,
                                district_id,
                                district_state.expansions,
                            ),
                            district_id,
                            district_state,
                        )
                    )

        if candidates:
            _, _, district_id, district_state = max(candidates)
            if self._expand_district(world, district_id, district_state):
                state.visible_city_expansions += 1
                district_state.last_expansion_tick = world.tick
                self._history(
                    world,
                    "city",
                    "District expansion",
                    "housing and infrastructure pressure",
                    district_id,
                    district_state.infrastructure_load,
                )

        mood = world.autonomous_society.public_mood
        cohesion = world.autonomous_society.social_cohesion
        month_key = f"{world.clock.year:04d}-{world.clock.month:02d}"
        for org in state.organizations.values():
            previous = org.collective_action
            target = clamp((org.influence + org.resilience + mood + cohesion) / 4)
            org.collective_action = clamp(0.55 * previous + 0.45 * target)
            threshold = 0.58 + (stable(org.organization_id, month_key) % 8) / 100
            can_act = (
                org.collective_action >= threshold
                and org.last_action_month != month_key
                and stable(org.organization_id, month_key, "action") % 5 == 0
            )
            if can_act:
                org.action_active = True
                org.last_action_month = month_key
                state.collective_actions += 1
                self._history(
                    world,
                    "organization",
                    "Collective action",
                    org.kind,
                    org.organization_id,
                    org.collective_action,
                )
            elif org.action_active and org.collective_action < threshold - 0.08:
                org.action_active = False

        active_crises = len(world.civilization.crises.active)
        if active_crises > state.emergent_crises:
            state.emergent_crises = active_crises
            self._history(
                world,
                "emergence",
                "Crisis became historically significant",
                "world pressure",
                "civilization response",
                0.8,
            )

    def _yearly(self, world: Any) -> None:
        state = world.living_world_v2
        family_changes = education_changes = career_changes = 0
        for citizen_id, citizen in world.citizens.items():
            arc = state.citizen_arcs[citizen_id]
            new_family = self._family_role(world, citizen)
            new_education = self._education_stage(citizen.age)
            new_career = self._career_level(world, citizen_id)
            if new_family != arc.family_role:
                state.family_transitions += 1
                family_changes += 1
                arc.life_transitions += 1
            if new_education != arc.education_stage:
                state.education_transitions += 1
                education_changes += 1
                arc.life_transitions += 1
            if new_career != arc.career_level:
                state.career_transitions += 1
                career_changes += 1
                arc.life_transitions += 1
            arc.family_role = new_family
            arc.education_stage = new_education
            arc.career_level = new_career

        if family_changes or education_changes or career_changes:
            self._history(
                world,
                "citizen-life",
                "Annual life transitions",
                "aging, households and career development",
                f"family={family_changes}; education={education_changes}; career={career_changes}",
                clamp(
                    (family_changes + education_changes + career_changes)
                    / max(1, len(world.citizens))
                ),
            )
        self._history(
            world,
            "generation",
            "Annual civilization continuity",
            "citizen lives",
            "next world year",
            0.6,
        )

    def _expand_district(
        self, world: Any, district_id: str, district_state: UrbanDistrictState
    ) -> bool:
        district = world.geography.districts[district_id]
        index = district_state.expansions + 1
        location_id = f"v2-growth-{district_id}-{index}"
        if location_id in world.geography.locations:
            return False
        angle = stable(district_id, index) % 8
        dx = ((angle % 3) - 1) * (2.0 + index * 0.15)
        dy = (((angle // 3) % 3) - 1) * (2.0 + index * 0.15)
        location_type = LocationType.HOME if index % 2 else LocationType.PUBLIC
        world.geography.add_location(
            Location(
                location_id,
                district_id,
                f"{district.name} Growth {index}",
                location_type,
                Coordinate(
                    max(0.0, min(100.0, district.center.x + dx)),
                    max(0.0, min(100.0, district.center.y + dy)),
                ),
                240 if location_type == LocationType.HOME else 320,
                {
                    "generated_by": "living_world_v2",
                    "land_use": "housing"
                    if location_type == LocationType.HOME
                    else "infrastructure",
                },
            )
        )
        neighbors = [
            loc for loc in world.geography.district_locations(district_id) if loc.id != location_id
        ]
        if neighbors:
            world.geography.connect(
                location_id, neighbors[stable(location_id) % len(neighbors)].id, 4
            )
        district_state.expansions += 1
        world.events.append(
            DomainEvent(
                "LivingWorldCityExpanded",
                world.tick,
                {"district_id": district_id, "location_id": location_id},
            )
        )
        return True

    def _history(
        self, world: Any, category: str, title: str, cause: str, effect: str, significance: float
    ) -> None:
        state = world.living_world_v2
        state.timeline.append(
            TimelineRecord(
                len(state.timeline) + 1,
                world.tick,
                world.clock.year,
                world.clock.month,
                category,
                title,
                cause,
                effect,
                clamp(significance),
            )
        )
        state.timeline = state.timeline[-1024:]
        state.causal_chains += 1

    @staticmethod
    def _family_role(world: Any, citizen: Any) -> str:
        if citizen.household_id is None:
            return "independent"
        household = world.households.get(str(citizen.household_id))
        if household is None:
            household = next(
                (h for h in world.households.values() if h.id == citizen.household_id), None
            )
        if household is None:
            return "independent"
        members = [world.citizens.get(str(member)) for member in household.member_ids]
        ages = [m.age for m in members if m is not None]
        if citizen.age < 18:
            return "child"
        return "senior" if ages and citizen.age == max(ages) and citizen.age >= 55 else "adult"

    @staticmethod
    def _education_stage(age: int) -> str:
        if age < 6:
            return "early_childhood"
        if age < 18:
            return "school"
        if age < 25:
            return "higher_or_vocational"
        return "lifelong_learning"

    @staticmethod
    def _career_level(world: Any, citizen_id: str) -> str:
        profile = world.life_profiles.get(citizen_id)
        if profile is None:
            return "entry"
        progress = profile.career_progress
        if progress >= 0.75:
            return "lead"
        if progress >= 0.50:
            return "senior"
        if progress >= 0.25:
            return "mid"
        return "entry"

    @staticmethod
    def _employee_count(world: Any, business_id: Any) -> int:
        return sum(1 for c in world.citizens.values() if c.employer_id == business_id)

    def snapshot(self, world: Any) -> dict[str, object]:
        state = world.living_world_v2
        return {
            "version": "2.0.0",
            "milestone": "Living Digital World",
            "citizen_life": {
                "profiles": len(state.citizen_arcs),
                "family_transitions": state.family_transitions,
                "education_transitions": state.education_transitions,
                "career_transitions": state.career_transitions,
            },
            "organizations": {
                "total": len(state.organizations),
                "collective_actions": state.collective_actions,
            },
            "city": {
                "districts": len(state.urban_districts),
                "visible_expansions": state.visible_city_expansions,
                "locations": len(world.geography.locations),
            },
            "history": {
                "records": len(state.timeline),
                "causal_chains": state.causal_chains,
                "emergent_crises": state.emergent_crises,
            },
            "simulation": {
                "tick": world.tick,
                "long_run_cycles": state.long_run_cycles,
                "population": len(world.citizens),
                "businesses": len(world.businesses),
            },
            "human_review_authority_preserved": True,
        }
