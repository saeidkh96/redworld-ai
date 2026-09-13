from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class SimulationStepResponse(BaseModel):
    stepped: int
    world: dict[str, object]
