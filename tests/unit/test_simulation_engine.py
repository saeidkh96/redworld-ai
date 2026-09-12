from redworld.simulation.engine import SimulationEngine
from redworld.simulation.factory import create_genesis_world


def test_simulation_step_advances_tick() -> None:
    engine = SimulationEngine(create_genesis_world())

    assert engine.world.tick == 0

    engine.step()

    assert engine.world.tick == 1
