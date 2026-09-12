from dataclasses import dataclass, field
from uuid import UUID, uuid4

from redworld.domain.value_objects.money import Money


@dataclass(slots=True)
class Bank:
    name: str
    id: UUID = field(default_factory=uuid4)
    reserves: Money = field(default_factory=Money.zero)
