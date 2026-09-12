from decimal import Decimal

from redworld.core.events import DomainEvent, EventStore
from redworld.domain.entities.business import Business
from redworld.domain.entities.citizen import Citizen
from redworld.domain.value_objects.money import Money
from redworld.domains.accounting.ledger import Ledger
from redworld.domains.accounting.models import JournalEntry, Posting, PostingSide


class BusinessService:
    def produce(self, *, tick: int, business: Business, events: EventStore) -> Decimal:
        produced = business.productivity_per_employee * Decimal(len(business.employee_ids))
        business.inventory_units += produced
        events.append(
            DomainEvent(
                "GoodsProduced",
                tick,
                {"business_id": str(business.id), "units": str(produced)},
            )
        )
        return produced

    def purchase(
        self,
        *,
        tick: int,
        citizen: Citizen,
        business: Business,
        ledger: Ledger,
        events: EventStore,
    ) -> Money:
        if business.inventory_units <= 0:
            return Money.zero(ledger.currency)
        if citizen.cash_account_id is None or citizen.consumption_expense_account_id is None:
            raise ValueError("citizen accounts are not initialized")
        if business.cash_account_id is None or business.revenue_account_id is None:
            raise ValueError("business accounts are not initialized")

        available = ledger.balance(citizen.cash_account_id)
        budget = citizen.consumption_budget.min(available)
        if budget.amount <= 0:
            return Money.zero(ledger.currency)
        affordable_units = budget.amount / business.unit_price.amount
        units = min(Decimal("1"), affordable_units, business.inventory_units)
        if units <= 0:
            return Money.zero(ledger.currency)
        amount = Money(business.unit_price.amount * units, ledger.currency)
        entry = JournalEntry(
            tick=tick,
            description=f"Consumption: {citizen.name} buys from {business.name}",
            postings=(
                Posting(business.cash_account_id, PostingSide.DEBIT, amount),
                Posting(business.revenue_account_id, PostingSide.CREDIT, amount),
                Posting(citizen.consumption_expense_account_id, PostingSide.DEBIT, amount),
                Posting(citizen.cash_account_id, PostingSide.CREDIT, amount),
            ),
        )
        ledger.post(entry)
        business.inventory_units -= units
        business.total_units_sold += units
        citizen.last_consumption_tick = tick
        events.append(
            DomainEvent(
                "PurchaseCompleted",
                tick,
                {
                    "citizen_id": str(citizen.id),
                    "business_id": str(business.id),
                    "amount": str(amount.amount),
                },
            )
        )
        return amount


def business_profit(*, business: Business, ledger: Ledger) -> Money:
    if business.revenue_account_id is None or business.wage_expense_account_id is None:
        raise ValueError("business accounts are not initialized")
    if business.tax_expense_account_id is None:
        raise ValueError("business tax account is not initialized")
    revenue = ledger.balance(business.revenue_account_id)
    wages = ledger.balance(business.wage_expense_account_id)
    taxes = ledger.balance(business.tax_expense_account_id)
    return revenue - wages - taxes
