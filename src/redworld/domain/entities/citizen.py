from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from redworld.domain.value_objects.money import Money
from redworld.domains.life.models import CitizenNeeds, CitizenTraits, DailySchedule


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
    age: int = 30
    occupation: str = "Resident"
    home_location_id: str | None = None
    work_location_id: str | None = None
    current_location_id: str | None = None
    destination_location_id: str | None = None
    travel_path: list[str] = field(default_factory=list)
    needs: CitizenNeeds = field(default_factory=CitizenNeeds)
    traits: CitizenTraits = field(default_factory=CitizenTraits)
    schedule: DailySchedule = field(default_factory=DailySchedule)
    current_action: str = "idle"
    action_target_location_id: str | None = None
    last_action_tick: int = 0
    household_id: UUID | None = None

    @property
    def is_moving(self) -> bool:
        return bool(self.travel_path)
