from decimal import Decimal

import pytest

from redworld.domain.value_objects.money import Money


def test_money_rounds_to_cents() -> None:
    assert Money(Decimal("10.005")).amount == Decimal("10.00")
    assert Money(Decimal("10.015")).amount == Decimal("10.02")


def test_money_rejects_currency_mismatch() -> None:
    with pytest.raises(ValueError, match="currency mismatch"):
        _ = Money.of(1, "RWC") + Money.of(1, "EUR")


def test_money_multiplication() -> None:
    assert Money.of("2.50") * 4 == Money.of("10.00")
