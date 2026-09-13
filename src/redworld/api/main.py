from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from redworld import __version__
from redworld.api.routes.health import router as health_router
from redworld.api.routes.world import router as world_router
from redworld.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version=__version__, debug=settings.debug)
app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(world_router, prefix=settings.api_v1_prefix)

web_dir = Path(__file__).resolve().parents[1] / "web"
app.mount("/static", StaticFiles(directory=web_dir), name="static")


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/viewer")


@app.get("/viewer", include_in_schema=False)
def viewer() -> FileResponse:
    return FileResponse(web_dir / "index.html")
