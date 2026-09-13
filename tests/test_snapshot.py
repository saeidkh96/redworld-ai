from redworld.simulation.factory import create_world
from redworld.simulation.snapshot import map_snapshot


def test_snapshot_samples_render_agents_without_losing_population_count() -> None:
    world = create_world(population=1500)
    snap = map_snapshot(world, render_sample=75)
    assert snap["summary"]["population"] == 1500
    assert len(snap["agents"]) <= 75
    assert len(snap["districts"]) == 8
