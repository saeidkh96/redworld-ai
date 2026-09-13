from redworld.simulation.factory import create_world
from redworld.simulation.snapshot import map_snapshot


def test_buildings_attach_to_street_network() -> None:
    world = create_world(population=20, seed=7)
    home = next(
        location
        for location in world.geography.locations.values()
        if location.id.startswith("home-")
    )
    neighbors = {edge.target for edge in world.geography.adjacency[home.id]}
    assert any(node_id.startswith("street-") for node_id in neighbors)
    assert not any(node_id.startswith("hub-") for node_id in neighbors)


def test_snapshot_exposes_road_hierarchy() -> None:
    world = create_world(population=20, seed=7)
    roads = map_snapshot(world)["roads"]
    kinds = {road["kind"] for road in roads}
    assert {"arterial", "street", "access"} <= kinds
