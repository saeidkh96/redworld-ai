from functools import lru_cache

from redworld.core.config import get_settings
from redworld.simulation.engine import SimulationEngine
from redworld.simulation.factory import create_genesis_world


@lru_cache
def get_engine() -> SimulationEngine:
    settings = get_settings()
    world = create_genesis_world(settings.world_name)
    return SimulationEngine(world=world)
