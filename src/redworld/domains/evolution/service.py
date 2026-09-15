from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
from typing import TYPE_CHECKING

from redworld.core.events import DomainEvent
from redworld.domain.entities import Business, Citizen
from redworld.domain.value_objects.money import Money
from redworld.domains.accounting import Account, AccountType
from redworld.domains.geography import Coordinate, Location, LocationType
from redworld.domains.households import Household
from redworld.domains.life.progression import CitizenLifeProfile

if TYPE_CHECKING:
    from redworld.simulation.world_state import WorldState


def _stable_int(*parts: object) -> int:
    digest = sha256(":".join(map(str, parts)).encode()).digest()
    return int.from_bytes(digest[:8], "big")


class WorldEvolutionService:
    """Turns civilization aggregates into durable world-entity mutations.

    The service is deterministic for a world seed/time pair and intentionally caps
    monthly mutation volume so a long-running world evolves without tick spikes.
    """

    def yearly_life_events(self, world: WorldState) -> None:
        state = world.evolution
        year = world.clock.year
        if state.last_year_processed == year:
            return
        state.last_year_processed = year
        citizens = list(world.citizens.values())
        if not citizens:
            return

        target_births = min(
            24, max(0, int(len(citizens) * world.civilization.demography.fertility_rate))
        )
        senior = [c for c in citizens if c.age >= 72]
        target_deaths = min(
            18, max(0, int(len(citizens) * world.civilization.demography.mortality_rate))
        )
        target_marriages = min(20, max(0, int(len(citizens) * 0.004)))
        target_separations = min(
            10, max(0, int(len(citizens) * world.autonomous_society.polarization * 0.0015))
        )

        households = list(world.households.values())
        for index in range(target_births):
            household = households[_stable_int(world.seed, year, "birth", index) % len(households)]
            self._create_citizen(world, household, index)
        death_pool = (
            senior or sorted(citizens, key=lambda c: c.age, reverse=True)[: max(1, target_deaths)]
        )
        for citizen in death_pool[:target_deaths]:
            self._remove_citizen(world, citizen)
        self._realize_partnerships(world, target_marriages, target_separations)

    def monthly_economy(self, world: WorldState) -> None:
        state = world.evolution
        key = (world.clock.year, world.clock.month)
        if state.last_month_processed == key:
            return
        state.last_month_processed = key

        unemployed = [c for c in world.citizens.values() if not c.employed and c.age >= 18]
        businesses = list(world.businesses.values())
        confidence = world.civilization.economy.confidence_index
        hire_budget = min(20, int(len(unemployed) * max(0.0, confidence - 0.35) * 0.08))
        for citizen in unemployed[:hire_budget]:
            candidates = [b for b in businesses if len(b.employee_ids) < 80]
            if not candidates:
                break
            business = min(candidates, key=lambda b: (len(b.employee_ids), str(b.id)))
            try:
                world.employment.hire(
                    tick=world.tick,
                    citizen=citizen,
                    business=business,
                    wage=business.wage_offer,
                    events=world.events,
                )
                citizen.work_location_id = business.location_id
                state.hires_realized += 1
            except ValueError:
                pass

        if confidence < 0.34:
            employed = [c for c in world.citizens.values() if c.employed]
            for citizen in employed[: min(8, max(1, len(employed) // 250))]:
                self._layoff(world, citizen)

        if confidence >= 0.62 and len(world.businesses) < 80:
            self._create_business(world)
        elif confidence <= 0.28 and len(world.businesses) > 8:
            candidate = min(
                world.businesses.values(), key=lambda b: (len(b.employee_ids), str(b.id))
            )
            self._close_business(world, candidate)

        self._apply_policies(world)
        self._realize_city_developments(world)
        self._apply_crises(world)
        self._realize_migration(world)

    def _create_citizen(
        self,
        world: WorldState,
        household: Household,
        index: int,
        *,
        event_type: str = "CitizenBorn",
    ) -> Citizen:
        serial = len(world.citizens) + world.evolution.births_realized + 1
        citizen = Citizen(name=f"Citizen {serial:04d}", age=0)
        citizen.home_location_id = household.home_location_id
        citizen.current_location_id = household.home_location_id
        citizen.household_id = household.id
        household.member_ids.append(citizen.id)
        self._add_citizen_accounts(world, citizen)
        world.citizens[str(citizen.id)] = citizen
        world.life_profiles[str(citizen.id)] = CitizenLifeProfile()
        world.planning.seed_for(citizen)
        if event_type == "CitizenBorn":
            world.evolution.births_realized += 1
        world.events.append(
            DomainEvent(
                event_type,
                world.tick,
                {
                    "citizen_id": str(citizen.id),
                    "household_id": str(household.id),
                    "year": world.clock.year,
                },
            )
        )
        return citizen

    def _remove_citizen(
        self,
        world: WorldState,
        citizen: Citizen,
        *,
        event_type: str = "CitizenDied",
    ) -> None:
        for household in world.households.values():
            if citizen.id in household.member_ids:
                household.member_ids.remove(citizen.id)
        self._layoff(world, citizen, emit=False)
        world.citizens.pop(str(citizen.id), None)
        world.life_profiles.pop(str(citizen.id), None)
        world.autonomous_world.agents.pop(str(citizen.id), None)
        if event_type == "CitizenDied":
            world.evolution.deaths_realized += 1
        world.events.append(
            DomainEvent(
                event_type,
                world.tick,
                {
                    "citizen_id": str(citizen.id),
                    "age": citizen.age,
                    "year": world.clock.year,
                },
            )
        )

    def _realize_partnerships(self, world: WorldState, marriages: int, separations: int) -> None:
        adults = sorted(
            (c for c in world.citizens.values() if c.age >= 18), key=lambda c: str(c.id)
        )
        pairs = list(zip(adults[::2], adults[1::2], strict=False))
        for left, right in pairs[:marriages]:
            if left.household_id == right.household_id:
                continue
            household = world.households.get(str(left.household_id)) if left.household_id else None
            if household is None:
                household = Household(
                    left.home_location_id or right.home_location_id or "home-001", [left.id]
                )
                world.households[str(household.id)] = household
                left.household_id = household.id
            old = world.households.get(str(right.household_id)) if right.household_id else None
            if old and right.id in old.member_ids:
                old.member_ids.remove(right.id)
            if right.id not in household.member_ids:
                household.member_ids.append(right.id)
            right.household_id = household.id
            right.home_location_id = household.home_location_id
            world.evolution.marriages_realized += 1
            world.events.append(
                DomainEvent(
                    "HouseholdPartnershipFormed",
                    world.tick,
                    {
                        "citizen_ids": [str(left.id), str(right.id)],
                        "household_id": str(household.id),
                    },
                )
            )
        multi = [h for h in world.households.values() if len(h.member_ids) >= 2]
        for household in multi[:separations]:
            departing_id = household.member_ids.pop()
            citizen = world.citizens.get(str(departing_id))
            if citizen is None:
                continue
            new_household = Household(household.home_location_id, [citizen.id])
            world.households[str(new_household.id)] = new_household
            citizen.household_id = new_household.id
            world.evolution.separations_realized += 1
            world.events.append(
                DomainEvent(
                    "HouseholdSeparated",
                    world.tick,
                    {
                        "citizen_id": str(citizen.id),
                        "household_id": str(new_household.id),
                    },
                )
            )

    def _add_citizen_accounts(self, world: WorldState, citizen: Citizen) -> None:
        citizen.cash_account_id = world.ledger.add_account(
            Account(f"{citizen.name}: cash", AccountType.ASSET, citizen.id)
        )
        citizen.income_account_id = world.ledger.add_account(
            Account(f"{citizen.name}: income", AccountType.REVENUE, citizen.id)
        )
        citizen.consumption_expense_account_id = world.ledger.add_account(
            Account(f"{citizen.name}: consumption", AccountType.EXPENSE, citizen.id)
        )
        citizen.tax_expense_account_id = world.ledger.add_account(
            Account(f"{citizen.name}: tax", AccountType.EXPENSE, citizen.id)
        )

    def _layoff(self, world: WorldState, citizen: Citizen, emit: bool = True) -> None:
        if not citizen.employed:
            return
        for contract in world.employment.contracts.values():
            if contract.citizen_id == citizen.id and contract.active:
                contract.active = False
        if citizen.employer_id:
            business = world.businesses.get(str(citizen.employer_id))
            if business and citizen.id in business.employee_ids:
                business.employee_ids.remove(citizen.id)
        citizen.employed = False
        citizen.employer_id = None
        citizen.work_location_id = None
        citizen.wage_per_tick = Money.zero(world.ledger.currency)
        world.evolution.layoffs_realized += 1
        if emit:
            world.events.append(
                DomainEvent("CitizenLaidOff", world.tick, {"citizen_id": str(citizen.id)})
            )

    def _create_business(self, world: WorldState) -> Business | None:
        owners = [c for c in world.citizens.values() if c.age >= 21]
        if not owners:
            return None
        owner = owners[
            _stable_int(world.seed, world.clock.year, world.clock.month, "startup") % len(owners)
        ]
        number = world.evolution.businesses_created + len(world.businesses) + 1
        business = Business(name=f"Genesis Venture {number:03d}", owner_id=owner.id)
        work_locations = [
            location
            for location in world.geography.locations.values()
            if location.location_type == LocationType.WORKPLACE
        ]
        if work_locations:
            business.location_id = work_locations[number % len(work_locations)].id
        business.cash_account_id = world.ledger.add_account(
            Account(f"{business.name}: cash", AccountType.ASSET, business.id)
        )
        business.revenue_account_id = world.ledger.add_account(
            Account(f"{business.name}: revenue", AccountType.REVENUE, business.id)
        )
        business.wage_expense_account_id = world.ledger.add_account(
            Account(f"{business.name}: wages", AccountType.EXPENSE, business.id)
        )
        business.tax_expense_account_id = world.ledger.add_account(
            Account(f"{business.name}: tax", AccountType.EXPENSE, business.id)
        )
        world.businesses[str(business.id)] = business
        world.evolution.businesses_created += 1
        world.events.append(
            DomainEvent(
                "BusinessCreated",
                world.tick,
                {"business_id": str(business.id), "owner_id": str(owner.id)},
            )
        )
        return business

    def _close_business(self, world: WorldState, business: Business) -> None:
        for citizen_id in list(business.employee_ids):
            citizen = world.citizens.get(str(citizen_id))
            if citizen:
                self._layoff(world, citizen)
        world.businesses.pop(str(business.id), None)
        world.autonomous_world.agents.pop(str(business.id), None)
        world.evolution.businesses_closed += 1
        world.events.append(
            DomainEvent("BusinessClosed", world.tick, {"business_id": str(business.id)})
        )

    def _apply_policies(self, world: WorldState) -> None:
        gov = world.government
        if gov is None:
            return
        for policy in world.civilization.governance.policies:
            key = f"{policy.year}:{policy.month}:{policy.name}"
            if not policy.active or key in world.evolution.applied_policy_keys:
                continue
            name = f"{policy.name} {policy.area}".lower()
            if "tax" in name or "revenue" in name:
                gov.income_tax_rate = max(
                    Decimal("0.03"), min(Decimal("0.25"), gov.income_tax_rate + Decimal("0.005"))
                )
            elif "welfare" in name or "social" in name or "health" in name:
                gov.welfare_payment = Money(
                    max(Decimal("1"), gov.welfare_payment.amount * Decimal("1.03")),
                    gov.welfare_payment.currency,
                )
            elif "business" in name or "econom" in name:
                gov.business_tax_rate = max(
                    Decimal("0.02"), gov.business_tax_rate - Decimal("0.002")
                )
            world.evolution.applied_policy_keys.add(key)
            world.evolution.policies_applied += 1
            world.events.append(
                DomainEvent("PolicyAppliedToWorld", world.tick, {"policy": policy.name})
            )

    def _realize_city_developments(self, world: WorldState) -> None:
        for development in world.civilization.city.developments:
            key = (
                f"{development.year}:{development.month}:"
                f"{development.district_id}:{development.project}"
            )
            if key in world.evolution.realized_developments:
                continue
            district = world.geography.districts.get(development.district_id)
            if district is None:
                continue
            suffix = len(world.evolution.realized_developments) + 1
            location_id = f"evolved-{development.district_id}-{suffix:03d}"
            x = max(0.0, min(100.0, district.center.x + ((suffix % 5) - 2) * 1.2))
            y = max(0.0, min(100.0, district.center.y + (((suffix // 5) % 5) - 2) * 1.2))
            world.geography.add_location(
                Location(
                    location_id,
                    district.id,
                    development.project,
                    LocationType.PUBLIC,
                    Coordinate(x, y),
                    250,
                )
            )
            hub = f"hub-{district.id}"
            if hub in world.geography.locations:
                world.geography.connect(location_id, hub, 3)
            world.evolution.realized_developments.add(key)
            world.evolution.city_projects_realized += 1
            world.events.append(
                DomainEvent(
                    "CityProjectRealized",
                    world.tick,
                    {"location_id": location_id, "district_id": district.id},
                )
            )

    def _realize_migration(self, world: WorldState) -> None:
        balance = world.civilization.city.migration_balance
        if balance == 0 or not world.households:
            return
        amount = min(4, abs(balance))
        if balance > 0:
            households = list(world.households.values())
            for index in range(amount):
                household = households[
                    _stable_int(world.seed, world.clock.year, world.clock.month, "migration", index)
                    % len(households)
                ]
                citizen = self._create_citizen(
                    world,
                    household,
                    1000 + index,
                    event_type="CitizenMigratedIn",
                )
                citizen.age = 18 + _stable_int(citizen.id, "age") % 43
                citizen.occupation = "New Resident"
                world.evolution.migrations_realized += 1
        else:
            candidates = sorted(
                (c for c in world.citizens.values() if c.age >= 18 and not c.employed),
                key=lambda c: str(c.id),
            )
            for citizen in candidates[:amount]:
                self._remove_citizen(
                    world,
                    citizen,
                    event_type="CitizenMigratedOut",
                )
                world.evolution.migrations_realized -= 1

    def _apply_crises(self, world: WorldState) -> None:
        current: dict[str, float] = {}
        for crisis in world.civilization.crises.active:
            key = f"{crisis.kind.value}:{crisis.started_year}:{crisis.started_month}"
            current[key] = crisis.severity
            if key not in world.evolution.active_shocks:
                world.evolution.crises_triggered += 1
                world.events.append(
                    DomainEvent(
                        "WorldCrisisTriggered",
                        world.tick,
                        {"kind": crisis.kind.value, "severity": crisis.severity},
                    )
                )
            if crisis.kind.value in {"recession", "shortage"}:
                for business in world.businesses.values():
                    business.productivity_per_employee = max(
                        Decimal("1"), business.productivity_per_employee * Decimal("0.995")
                    )
            elif crisis.kind.value in {"epidemic", "disaster"}:
                for citizen in list(world.citizens.values())[::50]:
                    citizen.needs.health = min(1.0, citizen.needs.health + crisis.severity * 0.03)
        world.evolution.active_shocks = current
