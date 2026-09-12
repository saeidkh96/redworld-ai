from fastapi import APIRouter

from redworld import __version__
from redworld.api.schemas import HealthResponse
from redworld.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=__version__,
    )
