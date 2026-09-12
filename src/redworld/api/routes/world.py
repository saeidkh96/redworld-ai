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
        ledger_entries=world.ledger.audit_entry_count(),
        events=len(world.events.events),
        household_cash=str(world.economy.total_household_cash.amount),
        business_cash=str(world.economy.total_business_cash.amount),
        bank_cash=str(world.economy.total_bank_cash.amount),
        government_cash=str(world.economy.government_cash.amount),
        unemployment_rate=world.economy.unemployment_rate,
    )


@router.get("", response_model=WorldSummaryResponse)
def get_world(engine: EngineDependency) -> WorldSummaryResponse:
    return _summary(engine.world)


@router.post("/step", response_model=SimulationStepResponse)
def step_world(engine: EngineDependency) -> SimulationStepResponse:
    world = engine.step()
    summary = _summary(world)
    return SimulationStepResponse(**summary.model_dump(), stepped=True)
