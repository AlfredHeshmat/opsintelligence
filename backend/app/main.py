import logging
from collections.abc import AsyncIterator
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
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def protect_enterprise_responses(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith('/api/v1/enterprise'):
            response.headers['Cache-Control'] = 'no-store'
            response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    app.include_router(router)
    app.include_router(operations_router)
    app.include_router(intelligence_router)
    app.include_router(workspace_router)
    app.include_router(enterprise_router)
    app.include_router(connectors_router)
    app.include_router(industry_pilots_router)
    return app
