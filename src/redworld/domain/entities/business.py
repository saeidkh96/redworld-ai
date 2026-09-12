from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from redworld.domain.value_objects.money import Money


@dataclass(slots=True)
class Business:
    name: str
    owner_id: UUID
    id: UUID = field(default_factory=uuid4)
    cash: Money = field(default_factory=Money.zero)
    employee_ids: list[UUID] = field(default_factory=list)
    cash_account_id: UUID | None = None
    revenue_account_id: UUID | None = None
    wage_expense_account_id: UUID | None = None
    tax_expense_account_id: UUID | None = None
    wage_offer: Money = field(default_factory=lambda: Money.of("20.00"))
    unit_price: Money = field(default_factory=lambda: Money.of("4.00"))
    productivity_per_employee: Decimal = Decimal("4")
    inventory_units: Decimal = Decimal("0")
    total_units_sold: Decimal = Decimal("0")
