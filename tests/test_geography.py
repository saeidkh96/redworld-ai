from redworld.simulation.factory import create_world


def test_genesis_city_has_expected_foundation() -> None:
    world = create_world(population=25)
    assert "genesis-city" in world.geography.cities
    assert len(world.geography.districts) == 8
    assert len(world.geography.locations) > 90


def test_spatial_graph_routes_between_home_and_work() -> None:
    world = create_world(population=25)
    citizen = next(c for c in world.citizens.values() if c.employed)
    path = world.geography.shortest_path(citizen.home_location_id, citizen.work_location_id)
    assert path[0] == citizen.home_location_id
    assert path[-1] == citizen.work_location_id
    assert len(path) >= 3
