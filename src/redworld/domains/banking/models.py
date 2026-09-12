from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal
from uuid import UUID, uuid4

from redworld.domain.value_objects.money import Money


@dataclass(frozen=True, slots=True)
class DepositAccount:
    bank_id: UUID
    owner_id: UUID
    ledger_account_id: UUID
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class Loan:
    bank_id: UUID
    borrower_id: UUID
    principal: Money
    annual_interest_rate: Decimal
    remaining_principal: Money
    term_ticks: int = 12
    ticks_elapsed: int = 0
    id: UUID = field(default_factory=uuid4)
    active: bool = True

    def scheduled_principal_payment(self) -> Money:
        remaining_ticks = max(self.term_ticks - self.ticks_elapsed, 1)
        amount = (self.remaining_principal.amount / Decimal(remaining_ticks)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )
        return Money(amount, self.remaining_principal.currency)
