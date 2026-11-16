import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router
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
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app
