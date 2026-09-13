from functools import lru_cache

from redworld.core.config import get_settings
from redworld.simulation import SimulationEngine, create_world


@lru_cache
def get_engine() -> SimulationEngine:
    settings = get_settings()
    world = create_world(
        population=settings.default_population,
        seed=settings.world_seed,
    )
    return SimulationEngine(world)
