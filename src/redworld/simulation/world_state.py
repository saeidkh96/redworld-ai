from dataclasses import dataclass, field

from redworld.domain.entities import Bank, Business, Citizen, Economy, Government


@dataclass(slots=True)
class WorldState:
    name: str
    tick: int = 0
    citizens: dict[str, Citizen] = field(default_factory=dict)
    businesses: dict[str, Business] = field(default_factory=dict)
    banks: dict[str, Bank] = field(default_factory=dict)
    government: Government | None = None
    economy: Economy = field(default_factory=Economy)
