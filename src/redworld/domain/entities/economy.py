from dataclasses import dataclass, field

from redworld.domain.value_objects.money import Money


@dataclass(slots=True)
class Economy:
    currency: str = "RWC"
    gross_output: Money = field(default_factory=Money.zero)
    total_household_cash: Money = field(default_factory=Money.zero)
    total_business_cash: Money = field(default_factory=Money.zero)
    total_bank_cash: Money = field(default_factory=Money.zero)
    government_cash: Money = field(default_factory=Money.zero)
    total_wages: Money = field(default_factory=Money.zero)
    total_consumption: Money = field(default_factory=Money.zero)
    total_taxes: Money = field(default_factory=Money.zero)
    unemployment_rate: float = 0.0
