import logging
import time
from collections import deque
from collections.abc import AsyncIterator
from threading import Lock

from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router
from app.api.operations import router as operations_router
from app.api.intelligence import router as intelligence_router
from app.api.workspace import router as workspace_router
from app.api.enterprise import router as enterprise_router
from app.api.connectors import router as connectors_router
from app.api.industry_pilots import router as industry_pilots_router
from app.api.project_data import router as project_data_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import create_database_engine

logger = logging.getLogger("opsintelligence.application")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.engine = create_database_engine(settings)
        logger.info("Application started")

        try:
            yield
        finally:
            app.state.engine.dispose()
            logger.info("Application stopped")

    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def protect_enterprise_responses(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith('/api/v1/enterprise'):
            response.headers['Cache-Control'] = 'no-store'
            response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    if settings.ops_public_demo_only:
        # Best-effort process-local budget for the intentionally public, bounded
        # demo calculations. Not a substitute for edge rate limiting / WAF.
        recent_writes: deque[float] = deque()
        writes_lock = Lock()

        @app.middleware("http")
        async def restrict_public_demo(request, call_next):
            path = request.url.path
            if path.startswith("/api/v1/enterprise"):
                return JSONResponse(status_code=404, content={"detail": "Enterprise APIs are not deployed on this public demo"})
            if path == "/api/v1/data/seed":
                return JSONResponse(status_code=403, content={"detail": "Public demo data is fixed; reset is disabled"})
            if request.method not in ("GET", "HEAD", "OPTIONS"):
                now = time.monotonic()
                with writes_lock:
                    while recent_writes and now - recent_writes[0] > 60:
                        recent_writes.popleft()
                    if len(recent_writes) >= 30:
                        return JSONResponse(status_code=429, content={"detail": "Demo computation limit reached; please try again later"}, headers={"Retry-After": "60"})
                    recent_writes.append(now)
            return await call_next(request)

    app.include_router(router)
    app.include_router(operations_router)
    app.include_router(intelligence_router)
    app.include_router(workspace_router)
    if not settings.ops_public_demo_only:
        app.include_router(enterprise_router)
        app.include_router(connectors_router)
    app.include_router(industry_pilots_router)
    if not settings.ops_public_demo_only:
        app.include_router(project_data_router)
    return app
