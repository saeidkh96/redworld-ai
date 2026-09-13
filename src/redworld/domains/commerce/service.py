from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from redworld.core.events import DomainEvent, EventStore
from redworld.domain.entities import Business, Citizen
from redworld.domain.value_objects.money import Money
from redworld.domains.accounting import Ledger
from redworld.domains.businesses import BusinessService
from redworld.domains.commerce.models import MarketState


@dataclass(slots=True)
class CommerceService:
    market: MarketState = field(default_factory=MarketState)

    def restock(self, *, day: int, businesses: list[Business]) -> None:
        if day == self.market.last_restock_day:
            return
        produced = sum((business.inventory_units for business in businesses), Decimal("0"))
        self.market.food_units = min(Decimal("10000"), self.market.food_units + produced)
        self.market.last_restock_day = day

    def purchase_food(
        self,
        *,
        tick: int,
        citizen: Citizen,
        businesses: list[Business],
        ledger: Ledger,
        events: EventStore,
    ) -> Money:
        if self.market.food_units <= 0 or not businesses:
            return Money.zero(ledger.currency)
        seller = businesses[citizen.id.int % len(businesses)]
        if seller.inventory_units <= 0:
            seller.inventory_units += Decimal("8")
        amount = BusinessService().purchase(
            tick=tick, citizen=citizen, business=seller, ledger=ledger, events=events
        )
        if amount.amount > 0:
            self.market.food_units = max(Decimal("0"), self.market.food_units - Decimal("1"))
            events.append(
                DomainEvent(
                    "FoodPurchased",
                    tick,
                    {"citizen_id": str(citizen.id), "business_id": str(seller.id)},
                )
            )
        return amount
