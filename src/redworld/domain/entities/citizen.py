from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from redworld.domain.value_objects.money import Money


@dataclass(slots=True)
class Citizen:
    name: str
    id: UUID = field(default_factory=uuid4)
    cash: Money = field(default_factory=Money.zero)
    employed: bool = False
    employer_id: UUID | None = None
    wage_per_tick: Money = field(default_factory=Money.zero)
    consumption_budget: Money = field(default_factory=lambda: Money.of("8.00"))
    cash_account_id: UUID | None = None
    income_account_id: UUID | None = None
    consumption_expense_account_id: UUID | None = None
    tax_expense_account_id: UUID | None = None
    consumption_need_units: Decimal = Decimal("1")
    last_consumption_tick: int | None = None
