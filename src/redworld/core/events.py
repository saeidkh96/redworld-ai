from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class DomainEvent:
    event_type: str
    tick: int
    payload: dict[str, Any]
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class EventStore:
    events: list[DomainEvent] = field(default_factory=list)

    def append(self, event: DomainEvent) -> None:
        self.events.append(event)

    def since(self, tick: int) -> list[DomainEvent]:
        return [event for event in self.events if event.tick >= tick]
