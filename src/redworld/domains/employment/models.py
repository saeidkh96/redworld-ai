from dataclasses import dataclass, field
from uuid import UUID, uuid4

from redworld.domain.value_objects.money import Money


@dataclass(slots=True)
class EmploymentContract:
    citizen_id: UUID
    business_id: UUID
    wage_per_tick: Money
    active: bool = True
    id: UUID = field(default_factory=uuid4)
