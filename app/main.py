"""GCG Ticketing System — FastAPI application entry point."""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings

# APScheduler is not compatible with Vercel serverless — skip it there
_IS_SERVERLESS = os.environ.get("VERCEL") == "1"
if not _IS_SERVERLESS:
    from app.scheduler import scheduler

# Import all route modules
from app.api.routes import (
    auth,
    users,
    tickets,
    worklogs,
    properties,
    locations,
    assets,
    vendors,
    inventory,
    pm,
    categories,
    templates,
    incident_types,
    announcements,
    notifications,
    audit_logs,
    settings as settings_router,
    pricing,
    pcr,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: start/stop background scheduler."""
    logger.info("Starting GCG Ticketing System API")
    if not _IS_SERVERLESS:
        scheduler.start()
    yield
    logger.info("Shutting down GCG Ticketing System API")
    if not _IS_SERVERLESS:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="GCG Ticketing System API",
    description="Hotel maintenance and facilities management ticketing platform",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static file serving for uploaded photos / assets (local only)
# ---------------------------------------------------------------------------
if os.path.isdir("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ---------------------------------------------------------------------------
# Routers  — all prefixed with /api
# ---------------------------------------------------------------------------
_API_PREFIX = "/api"

app.include_router(auth.router, prefix=_API_PREFIX)
app.include_router(users.router, prefix=_API_PREFIX)
app.include_router(tickets.router, prefix=_API_PREFIX)
app.include_router(worklogs.router, prefix=_API_PREFIX)
app.include_router(properties.router, prefix=_API_PREFIX)
app.include_router(locations.router, prefix=_API_PREFIX)
app.include_router(assets.router, prefix=_API_PREFIX)
app.include_router(vendors.router, prefix=_API_PREFIX)
app.include_router(inventory.router, prefix=_API_PREFIX)
app.include_router(pm.router, prefix=_API_PREFIX)
app.include_router(categories.router, prefix=_API_PREFIX)
app.include_router(templates.router, prefix=_API_PREFIX)
app.include_router(incident_types.router, prefix=_API_PREFIX)
app.include_router(announcements.router, prefix=_API_PREFIX)
app.include_router(notifications.router, prefix=_API_PREFIX)
app.include_router(audit_logs.router, prefix=_API_PREFIX)
app.include_router(settings_router.router, prefix=_API_PREFIX)
app.include_router(pricing.router, prefix=_API_PREFIX)
app.include_router(pcr.router, prefix=_API_PREFIX)


@app.get("/health", tags=["health"])
async def health_check():
    """Basic liveness probe."""
    return {"status": "ok", "service": "GCG Ticketing System API"}
