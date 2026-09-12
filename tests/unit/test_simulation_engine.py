import pytest

from redworld.simulation.engine import SimulationEngine
from redworld.simulation.factory import create_genesis_world


def test_step_advances_world_tick() -> None:
    engine = SimulationEngine(create_genesis_world())
    assert engine.step().tick == 1


def test_run_rejects_negative_ticks() -> None:
    engine = SimulationEngine(create_genesis_world())
    with pytest.raises(ValueError, match="non-negative"):
        engine.run(-1)
