from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from redworld.domain.value_objects.money import Money


@dataclass(slots=True)
class Government:
    name: str
    id: UUID = field(default_factory=uuid4)
    treasury: Money = field(default_factory=Money.zero)
    treasury_account_id: UUID | None = None
    tax_revenue_account_id: UUID | None = None
    spending_expense_account_id: UUID | None = None
    income_tax_rate: Decimal = Decimal("0.10")
    business_tax_rate: Decimal = Decimal("0.08")
    welfare_payment: Money = field(default_factory=lambda: Money.of("5.00"))
