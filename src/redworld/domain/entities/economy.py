from dataclasses import dataclass

from redworld.domain.value_objects.money import Money


@dataclass(slots=True)
class Economy:
    currency: str = "RWC"
    gross_output: Money = Money.zero()
    total_household_cash: Money = Money.zero()
    total_business_cash: Money = Money.zero()
