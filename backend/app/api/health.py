import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.services.readiness import check_database

router = APIRouter(prefix="/api/v1", tags=["system"])
logger = logging.getLogger("opsintelligence.readiness")


class HealthResponse(BaseModel):
    status: Literal["healthy"] = "healthy"


class ReadinessResponse(BaseModel):
    status: Literal["ready", "unavailable"]
    database: Literal["connected", "unavailable"]


def get_engine(request: Request) -> Engine:
    return request.app.state.engine


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.get("/ready", response_model=ReadinessResponse)
def ready(
    response: Response,
    engine: Annotated[Engine, Depends(get_engine)],
) -> ReadinessResponse:
    try:
        check_database(engine)
    except SQLAlchemyError:
        # Exception details may contain credentials, so omit them.
        logger.warning("Database readiness check failed")
        response.status_code = 503
        return ReadinessResponse(
            status="unavailable",
            database="unavailable",
        )

    return ReadinessResponse(
        status="ready",
        database="connected",
    )
