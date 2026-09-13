from redworld.domains.mobility import MobilityService
from redworld.simulation.factory import create_world


def test_citizen_can_move_to_work() -> None:
    world = create_world(population=20, seed=7)
    citizen = next(c for c in world.citizens.values() if c.work_location_id is not None)
    service = MobilityService()
    assert citizen.work_location_id is not None
    service.request_move(
        tick=world.tick,
        citizen=citizen,
        destination_id=citizen.work_location_id,
        geography=world.geography,
        events=world.events,
    )
    while citizen.is_moving:
        service.advance(tick=world.tick, citizen=citizen, events=world.events)
    assert citizen.current_location_id == citizen.work_location_id
