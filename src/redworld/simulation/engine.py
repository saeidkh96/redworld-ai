from dataclasses import dataclass

from redworld.simulation.world_state import WorldState


@dataclass(slots=True)
class SimulationEngine:
    world: WorldState

    def step(self) -> WorldState:
        self.world.tick += 1
        return self.world
