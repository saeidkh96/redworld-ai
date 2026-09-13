from redworld.core.events import DomainEvent


def citizen_moved(tick: int, citizen_id: str, source: str, target: str) -> DomainEvent:
    return DomainEvent(
        "CitizenMoved",
        tick,
        {"citizen_id": citizen_id, "source": source, "target": target},
    )


def citizen_arrived(tick: int, citizen_id: str, location_id: str) -> DomainEvent:
    return DomainEvent(
        "CitizenArrived",
        tick,
        {"citizen_id": citizen_id, "location_id": location_id},
    )
