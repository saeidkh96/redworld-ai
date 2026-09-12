from decimal import Decimal

import pytest

from redworld.domain.value_objects.money import Money


def test_money_normalizes_to_cents() -> None:
    money = Money(Decimal("10.126"), "rwc")

    assert money.amount == Decimal("10.13")
    assert money.currency == "RWC"


def test_money_addition_requires_same_currency() -> None:
    left = Money(Decimal("10.00"), "RWC")
    right = Money(Decimal("2.50"), "RWC")

    assert left + right == Money(Decimal("12.50"), "RWC")


def test_money_rejects_cross_currency_arithmetic() -> None:
    with pytest.raises(ValueError, match="currency mismatch"):
        _ = Money(Decimal("1.00"), "RWC") + Money(Decimal("1.00"), "EUR")
