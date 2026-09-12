from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from redworld.domain.value_objects.money import Money


@dataclass(slots=True)
class Bank:
    name: str
    id: UUID = field(default_factory=uuid4)
    reserves: Money = field(default_factory=Money.zero)
    cash_account_id: UUID | None = None
    interest_revenue_account_id: UUID | None = None
    max_loan_to_reserves_ratio: Decimal = Decimal("0.50")
