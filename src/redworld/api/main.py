from fastapi import FastAPI

from redworld import __version__
from redworld.api.routes.health import router as health_router
from redworld.api.routes.world import router as world_router
from redworld.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    debug=settings.debug,
)

app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(world_router, prefix=settings.api_v1_prefix)
