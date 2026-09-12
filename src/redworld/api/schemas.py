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
    ledger_entries: int
    events: int
    household_cash: str
    business_cash: str
    bank_cash: str
    government_cash: str
    unemployment_rate: float


class SimulationStepResponse(WorldSummaryResponse):
    stepped: bool
