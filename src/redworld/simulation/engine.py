from dataclasses import dataclass

from redworld.core.events import DomainEvent
from redworld.domain.value_objects.money import Money
from redworld.domains.businesses import BusinessService
from redworld.domains.economy import refresh_economy_metrics
from redworld.domains.government import GovernmentService
from redworld.simulation.world_state import WorldState


@dataclass(slots=True)
class SimulationEngine:
    world: WorldState

    def step(self) -> WorldState:
        self.world.tick += 1
        tick = self.world.tick
        business_service = BusinessService()
        government_service = GovernmentService()
        total_wages = Money.zero(self.world.ledger.currency)
        total_consumption = Money.zero(self.world.ledger.currency)
        total_taxes = Money.zero(self.world.ledger.currency)

        for business in self.world.businesses.values():
            business_service.produce(
                tick=tick,
                business=business,
                events=self.world.events,
            )

        for contract in self.world.employment.active_contracts():
            citizen = self.world.citizens[str(contract.citizen_id)]
            business = self.world.businesses[str(contract.business_id)]
            if business.cash_account_id is None:
                raise ValueError("business cash account missing")
            business_cash = self.world.ledger.balance(business.cash_account_id)
            if business_cash.amount < contract.wage_per_tick.amount:
                self.world.events.append(
                    DomainEvent(
                        "PayrollSkipped",
                        tick,
                        {"business_id": str(business.id)},
                    )
                )
                continue
            entry = self.world.employment.payroll_entry(
                tick=tick,
                contract=contract,
                citizen=citizen,
                business=business,
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
        self.world.economy.gross_output = (
            self.world.economy.gross_output + total_consumption
        )
        refresh_economy_metrics(self.world)
        self.world.events.append(DomainEvent("WorldTickCompleted", tick, {"tick": tick}))
        return self.world

    def run(self, ticks: int) -> WorldState:
        if ticks < 0:
            raise ValueError("ticks must be non-negative")
        for _ in range(ticks):
            self.step()
        return self.world
