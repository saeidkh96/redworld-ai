from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class WorldSummaryResponse(BaseModel):
    name: str
    tick: int
    citizens: int
    businesses: int
    banks: int
    has_government: bool
    currency: str


class SimulationStepResponse(WorldSummaryResponse):
    stepped: bool
