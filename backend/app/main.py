"""
EcoNodeX FastAPI application.
Serves the React frontend as static files in production.
"""
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import FRONTEND_DIST
from .database import init_db
from .seed import seed
from .routers import (
    analyses,
    exports,
    locations,
    media,
    methods,
    projects,
    records,
    sampling,
    taxa,
    uploads,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    seed()
    yield


app = FastAPI(
    title="EcoNodeX",
    description="Gestión local de datos ecológicos — MVP #1",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow same-LAN cross-origin requests (e.g., phone accessing the upload page)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
for router_module in [
    projects, locations, taxa, methods, sampling, records,
    media, uploads, analyses, exports,
]:
    app.include_router(router_module.router)


# ---------------------------------------------------------------------------
# Serve React SPA (static files from frontend/dist)
# ---------------------------------------------------------------------------

_DIST = FRONTEND_DIST

if _DIST.exists():
    # Mount static assets (JS, CSS, images, etc.) from dist/assets
    assets_dir = _DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/", include_in_schema=False)
    async def root():
        return FileResponse(str(_DIST / "index.html"))

    @app.get("/upload", include_in_schema=False)
    @app.get("/upload/{_:path}", include_in_schema=False)
    async def serve_upload(_: str = ""):
        return FileResponse(str(_DIST / "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        candidate = _DIST / full_path
        if candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(_DIST / "index.html"))
