from __future__ import annotations

from redworld.core.events import EventStore
from redworld.domain.entities import Citizen
from redworld.domains.geography.events import citizen_arrived, citizen_moved
from redworld.domains.geography.service import GeographyService


class MobilityService:
    def request_move(
        self,
        *,
        tick: int,
        citizen: Citizen,
        destination_id: str,
        geography: GeographyService,
        events: EventStore,
    ) -> None:
        if citizen.current_location_id is None:
            raise ValueError("citizen has no current location")

        path = geography.shortest_path(citizen.current_location_id, destination_id)
        citizen.destination_location_id = destination_id
        citizen.travel_path = path[1:]
        if not citizen.travel_path:
            citizen.destination_location_id = None
            events.append(citizen_arrived(tick, str(citizen.id), destination_id))

    def advance(self, *, tick: int, citizen: Citizen, events: EventStore) -> None:
        if not citizen.travel_path or citizen.current_location_id is None:
            return

        source = citizen.current_location_id
        target = citizen.travel_path.pop(0)
        citizen.current_location_id = target
        events.append(citizen_moved(tick, str(citizen.id), source, target))
        if not citizen.travel_path:
            citizen.destination_location_id = None
            events.append(citizen_arrived(tick, str(citizen.id), target))
