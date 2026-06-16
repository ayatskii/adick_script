"""FastAPI application entrypoint.

Mounts the run + data routers, configures CORS for the Vite dev server, and
serves /api/health (which reports phase0_done = no "# CONFIRM" left in
edvibe_bot/selectors.py, and openai_key_set).
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config as backend_config
from .routes import data as data_routes
from .routes import runs as runs_routes
from .schemas import HealthResponse

app = FastAPI(
    title="Edvibe Grader Backend",
    version="1.0",
    description="REST + WS bridge between the React frontend and the edvibe_bot core.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=backend_config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs_routes.router)
app.include_router(data_routes.router)


def _selectors_path() -> str:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(here, "edvibe_bot", "selectors.py")


def phase0_done() -> bool:
    """Phase 0 is done when no '# CONFIRM' marker remains in selectors.py."""
    path = _selectors_path()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return "# CONFIRM" not in fh.read()
    except OSError:
        # If we can't read it, we can't assert Phase 0 is done.
        return False


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        ok=True,
        phase0_done=phase0_done(),
        openai_key_set=backend_config.openai_key_set(),
    )
