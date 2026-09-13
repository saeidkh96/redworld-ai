from dataclasses import dataclass

from redworld.core.events import DomainEvent
from redworld.domain.value_objects.money import Money
from redworld.domains.actions import ActionService
from redworld.domains.autonomy import AutonomousSocietyService
from redworld.domains.businesses import BusinessService
from redworld.domains.civilization import LivingCivilizationService
from redworld.domains.decisions import DecisionService
from redworld.domains.economy import refresh_economy_metrics
from redworld.domains.government import GovernmentService
from redworld.domains.life.progression import CitizenLifeProfile, CitizenProgressionService
from redworld.domains.life.service import LifeService
from redworld.domains.mobility import MobilityService
from redworld.simulation.world_state import WorldState


@dataclass(slots=True)
class SimulationEngine:
    world: WorldState

    def __post_init__(self) -> None:
        self._bootstrap_living_world()

    def _bootstrap_living_world(self) -> None:
        if not self.world.geography.locations:
            return

        citizens = list(self.world.citizens.values())

        for citizen in citizens:
            self.world.life_profiles.setdefault(str(citizen.id), CitizenLifeProfile())

        AutonomousSocietyService().bootstrap(
            self.world.autonomous_society,
            citizens,
        )

        LivingCivilizationService().bootstrap(
            state=self.world.civilization,
            citizens=citizens,
            profiles=self.world.life_profiles,
            society=self.world.autonomous_society,
            tick=self.world.tick,
            year=self.world.clock.year,
            month=self.world.clock.month,
            events=self.world.events,
        )

    def step(self) -> WorldState:
        if self.world.geography.locations:
            return self._step_living_world()
        return self._step_legacy_closed_economy()

    def _step_living_world(self) -> WorldState:
        self.world.tick += 1
        self.world.clock.advance()
        tick = self.world.tick
        minute = self.world.clock.minute_of_day
        business_service = BusinessService()
        life_service = LifeService()
        action_service = ActionService()
        decision_service = DecisionService()
        mobility = MobilityService()
        businesses = list(self.world.businesses.values())
        progression = CitizenProgressionService()
        autonomy = AutonomousSocietyService()
        civilization = LivingCivilizationService()
        self._bootstrap_living_world()
        self.world.commerce.restock(day=self.world.clock.day, businesses=businesses)
        if tick % 4 == 0:
            for business in businesses:
                business_service.produce(tick=tick, business=business, events=self.world.events)
        market_id = "market-square" if "market-square" in self.world.geography.locations else None
        park_id = "central-park" if "central-park" in self.world.geography.locations else None
        hospital_id = "city-hospital" if "city-hospital" in self.world.geography.locations else None
        for citizen in self.world.citizens.values():
            life_service.advance_needs(citizen, minute_of_day=minute)
            if citizen.is_moving:
                mobility.advance(tick=tick, citizen=citizen, events=self.world.events)
                if not citizen.is_moving:
                    action_service.complete_if_ready(world=self.world, citizen=citizen)
                continue
            if citizen.current_action != "idle":
                action_service.complete_if_ready(world=self.world, citizen=citizen)
                if citizen.current_action != "idle":
                    continue
            if (citizen.id.int + tick) % 2 != 0:
                continue
            proposal = decision_service.choose(
                citizen=citizen,
                minute_of_day=minute,
                market_location_id=market_id,
                park_location_id=park_id,
                hospital_location_id=hospital_id,
            )
            if proposal.action.value == "idle":
                continue
            action_service.start(world=self.world, citizen=citizen, proposal=proposal)
        if minute == 17 * 60 + 30:
            self._run_daily_payroll()
        if minute == 6 * 60 + 15 and self.world.government is not None:
            government_service = GovernmentService()
            for citizen in self.world.citizens.values():
                government_service.welfare(
                    tick=tick,
                    citizen=citizen,
                    government=self.world.government,
                    ledger=self.world.ledger,
                    events=self.world.events,
                )
        if tick % 16 == 0:
            for citizen in self.world.citizens.values():
                self.world.planning.update(citizen)
        if self.world.clock.minute_of_day == 0:
            for citizen in self.world.citizens.values():
                progression.daily_update(citizen, self.world.life_profiles[str(citizen.id)])
                if self.world.clock.day_of_month == 1 and self.world.clock.month == 1:
                    progression.yearly_update(
                        citizen,
                        self.world.life_profiles[str(citizen.id)],
                        year=self.world.clock.year,
                    )
            autonomy.daily_update(
                tick=tick,
                state=self.world.autonomous_society,
                citizens=list(self.world.citizens.values()),
                profiles=self.world.life_profiles,
                events=self.world.events,
            )
            civilization.daily_update(
                state=self.world.civilization,
                citizens=list(self.world.citizens.values()),
                profiles=self.world.life_profiles,
                society=self.world.autonomous_society,
                unemployment_rate=self.world.economy.unemployment_rate,
                tick=tick,
                year=self.world.clock.year,
                month=self.world.clock.month,
                events=self.world.events,
            )
            if self.world.clock.day_of_month == 1:
                civilization.monthly_update(
                    state=self.world.civilization,
                    citizens=list(self.world.citizens.values()),
                    society=self.world.autonomous_society,
                    unemployment_rate=self.world.economy.unemployment_rate,
                    district_ids=list(self.world.geography.districts),
                    tick=tick,
                    year=self.world.clock.year,
                    month=self.world.clock.month,
                    events=self.world.events,
                )
            if self.world.clock.day_of_month == 1 and self.world.clock.month == 1:
                civilization.yearly_update(
                    state=self.world.civilization,
                    citizens=list(self.world.citizens.values()),
                    society=self.world.autonomous_society,
                    tick=tick,
                    year=self.world.clock.year,
                    month=self.world.clock.month,
                    events=self.world.events,
                )
        refresh_economy_metrics(self.world)
        self.world.events.append(
            DomainEvent(
                "WorldTickCompleted",
                tick,
                {
                    "tick": tick,
                    "time": self.world.clock.label,
                    "population": len(self.world.citizens),
                },
            )
        )
        return self.world

    def _run_daily_payroll(self) -> None:
        government_service = GovernmentService()
        total_wages = Money.zero(self.world.ledger.currency)
        total_taxes = Money.zero(self.world.ledger.currency)
        for contract in self.world.employment.active_contracts():
            citizen = self.world.citizens.get(str(contract.citizen_id))
            business = self.world.businesses.get(str(contract.business_id))
            if citizen is None or business is None or business.cash_account_id is None:
                continue
            if (
                self.world.ledger.balance(business.cash_account_id).amount
                < contract.wage_per_tick.amount
            ):
                self.world.events.append(
                    DomainEvent(
                        "PayrollSkipped", self.world.tick, {"business_id": str(business.id)}
                    )
                )
                continue
            self.world.ledger.post(
                self.world.employment.payroll_entry(
                    tick=self.world.tick, contract=contract, citizen=citizen, business=business
                )
            )
            total_wages = total_wages + contract.wage_per_tick
            if self.world.government is not None:
                total_taxes = total_taxes + government_service.collect_income_tax(
                    tick=self.world.tick,
                    citizen=citizen,
                    government=self.world.government,
                    taxable_income=contract.wage_per_tick,
                    ledger=self.world.ledger,
                    events=self.world.events,
                )
        self.world.economy.total_wages = self.world.economy.total_wages + total_wages
        self.world.economy.total_taxes = self.world.economy.total_taxes + total_taxes

    def _step_legacy_closed_economy(self) -> WorldState:
        self.world.tick += 1
        self.world.clock.advance()
        tick = self.world.tick
        business_service = BusinessService()
        government_service = GovernmentService()
        total_wages = Money.zero(self.world.ledger.currency)
        total_consumption = Money.zero(self.world.ledger.currency)
        total_taxes = Money.zero(self.world.ledger.currency)
        for business in self.world.businesses.values():
            business_service.produce(tick=tick, business=business, events=self.world.events)
        for contract in self.world.employment.active_contracts():
            citizen = self.world.citizens[str(contract.citizen_id)]
            business = self.world.businesses[str(contract.business_id)]
            if business.cash_account_id is None:
                raise ValueError("business cash account missing")
            business_cash = self.world.ledger.balance(business.cash_account_id)
            if business_cash.amount < contract.wage_per_tick.amount:
                self.world.events.append(
                    DomainEvent("PayrollSkipped", tick, {"business_id": str(business.id)})
                )
                continue
            entry = self.world.employment.payroll_entry(
                tick=tick, contract=contract, citizen=citizen, business=business
            )
            self.world.ledger.post(entry)
            total_wages = total_wages + contract.wage_per_tick
            if self.world.government is not None:
                tax = government_service.collect_income_tax(
                    tick=tick,
                    citizen=citizen,
                    government=self.world.government,
                    taxable_income=contract.wage_per_tick,
                    ledger=self.world.ledger,
                    events=self.world.events,
                )
                total_taxes = total_taxes + tax
        businesses = list(self.world.businesses.values())
        if businesses:
            seller = businesses[0]
            for citizen in self.world.citizens.values():
                spent = business_service.purchase(
                    tick=tick,
                    citizen=citizen,
                    business=seller,
                    ledger=self.world.ledger,
                    events=self.world.events,
                )
                total_consumption = total_consumption + spent
        if self.world.government is not None:
            if businesses and total_consumption.amount > 0:
                business_tax = government_service.collect_business_tax(
                    tick=tick,
                    business=businesses[0],
                    government=self.world.government,
                    taxable_revenue=total_consumption,
                    ledger=self.world.ledger,
                    events=self.world.events,
                )
                total_taxes = total_taxes + business_tax
            for citizen in self.world.citizens.values():
                government_service.welfare(
                    tick=tick,
                    citizen=citizen,
                    government=self.world.government,
                    ledger=self.world.ledger,
                    events=self.world.events,
                )
        self.world.economy.total_wages = self.world.economy.total_wages + total_wages
        self.world.economy.total_consumption = (
            self.world.economy.total_consumption + total_consumption
        )
        self.world.economy.total_taxes = self.world.economy.total_taxes + total_taxes
        self.world.economy.gross_output = self.world.economy.gross_output + total_consumption
        refresh_economy_metrics(self.world)
        self.world.events.append(DomainEvent("WorldTickCompleted", tick, {"tick": tick}))
        return self.world

    def run(self, ticks: int) -> WorldState:
        if ticks < 0:
            raise ValueError("ticks must be non-negative")
        for _ in range(ticks):
            self.step()
        return self.world
