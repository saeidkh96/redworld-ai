from typing import Annotated

from fastapi import APIRouter, Depends

from redworld.api.dependencies import get_engine
from redworld.api.schemas import SimulationStepResponse, WorldSummaryResponse
from redworld.simulation.engine import SimulationEngine
from redworld.simulation.world_state import WorldState

router = APIRouter(prefix="/world", tags=["world"])

EngineDependency = Annotated[SimulationEngine, Depends(get_engine)]


def _summary(world: WorldState) -> WorldSummaryResponse:
    return WorldSummaryResponse(
        name=world.name,
        tick=world.tick,
        citizens=len(world.citizens),
        businesses=len(world.businesses),
        banks=len(world.banks),
        has_government=world.government is not None,
        currency=world.economy.currency,
    )


@router.get("", response_model=WorldSummaryResponse)
def get_world(engine: EngineDependency) -> WorldSummaryResponse:
    return _summary(engine.world)


@router.post("/step", response_model=SimulationStepResponse)
def step_world(engine: EngineDependency) -> SimulationStepResponse:
    world = engine.step()
    summary = _summary(world)

    return SimulationStepResponse(
        **summary.model_dump(),
        stepped=True,
    )