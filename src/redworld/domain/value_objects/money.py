from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

_CENT = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str = "RWC"

    def __post_init__(self) -> None:
        normalized_currency = self.currency.strip().upper()
        if not normalized_currency:
            raise ValueError("currency must not be empty")
        normalized_amount = Decimal(self.amount).quantize(_CENT, rounding=ROUND_HALF_EVEN)
        object.__setattr__(self, "currency", normalized_currency)
        object.__setattr__(self, "amount", normalized_amount)

    @classmethod
    def zero(cls, currency: str = "RWC") -> Money:
        return cls(Decimal("0.00"), currency)

    @classmethod
    def of(cls, amount: str | int | Decimal, currency: str = "RWC") -> Money:
        return cls(Decimal(amount), currency)

    def _ensure_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(f"currency mismatch: {self.currency} != {other.currency}")

    def __add__(self, other: Money) -> Money:
        self._ensure_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._ensure_same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, multiplier: int | Decimal) -> Money:
        return Money(self.amount * Decimal(multiplier), self.currency)

    def min(self, other: Money) -> Money:
        self._ensure_same_currency(other)
        return self if self.amount <= other.amount else other

    def is_negative(self) -> bool:
        return self.amount < 0

    def is_zero(self) -> bool:
        return self.amount == 0
