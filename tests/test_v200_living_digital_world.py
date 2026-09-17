from redworld.domains.living_world_v2 import LivingDigitalWorldService
from redworld.simulation.engine import SimulationEngine
from redworld.simulation.factory import create_world
from redworld.simulation.snapshot import (
    living_digital_world_snapshot,
    world_summary,
    world_timeline_snapshot,
)


def test_v200_bootstraps_deep_citizen_and_organization_state() -> None:
    world = create_world(population=80, seed=200)
    service = LivingDigitalWorldService()
    service.bootstrap(world)
    assert len(world.living_world_v2.citizen_arcs) == 80
    assert world.living_world_v2.organizations
    assert set(world.living_world_v2.urban_districts) == set(world.geography.districts)


def test_v200_runs_integrated_feedback_without_bypassing_hitl() -> None:
    world = create_world(population=80, seed=201)
    engine = SimulationEngine(world)
    engine.run(100)
    snapshot = living_digital_world_snapshot(world)
    assert snapshot["version"] == "2.0.0"
    assert snapshot["human_review_authority_preserved"] is True
    assert snapshot["citizen_life"]["profiles"] == len(world.citizens)
    assert snapshot["simulation"]["long_run_cycles"] >= 1


def test_v200_timeline_is_causal_and_bounded() -> None:
    world = create_world(population=80, seed=202)
    service = LivingDigitalWorldService()
    service.bootstrap(world)
    service._history(world, "test", "A consequence", "cause", "effect", 0.7)
    payload = world_timeline_snapshot(world, 10)
    assert payload["total"] == 1
    assert payload["items"][0]["cause"] == "cause"
    assert payload["items"][0]["effect"] == "effect"


def test_v200_world_reports_final_version() -> None:
    world = create_world(population=40, seed=203)
    assert world_summary(world)["version"] == "2.0.0"
