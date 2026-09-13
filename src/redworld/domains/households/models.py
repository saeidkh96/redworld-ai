from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from redworld.domain.value_objects.money import Money


@dataclass(slots=True)
class Household:
    home_location_id: str
    member_ids: list[UUID]
    id: UUID = field(default_factory=uuid4)
    monthly_rent: Money = field(default_factory=lambda: Money.of("900.00"))
