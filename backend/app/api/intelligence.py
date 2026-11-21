"""Product analytics, evaluated synthetic delay modelling, and scenario risk APIs."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.api.operations import get_db
from app.models import OptimizationRun
from app.services.prediction import current_report, train_model, predict_pending
from app.services.product_analytics import product_performance
from app.services.simulation import run_simulation

router = APIRouter(prefix="/api/v1", tags=["intelligence"])
DB = Annotated[Session, Depends(get_db)]


@router.get("/products/performance")
def products(db: DB, days: int = Query(30, ge=1, le=365), sku: str | None = None):
    try:
        return product_performance(db, days=days, sku=sku)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error


@router.post("/predictions/train")
def train(db: DB):
    try:
        return train_model(db)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error


@router.get("/predictions/model")
def model_report():
    return {"trained": current_report() is not None, "report": current_report()}


@router.get("/predictions/delays")
def delays(db: DB, sku: str | None = None, limit: int = Query(100, ge=1, le=200)):
    try:
        return predict_pending(db, sku=sku, limit=limit)
    except ValueError as error:
        raise HTTPException(409, str(error)) from error


class ScenarioRequest(BaseModel):
    optimization_run_id: int = Field(ge=1)
    trials: int = Field(default=1000, ge=100, le=5000)
    seed: int = 42
    delay_probability: float = Field(default=0.2, ge=0, le=1)
    late_penalty_per_unit: float = Field(default=8, ge=0, le=10000)
    shipping_cost_multiplier: float = Field(default=1.0, ge=0, le=10)


@router.post("/scenarios/compare")
def scenario(request: ScenarioRequest, db: DB):
    run = db.scalar(select(OptimizationRun).options(selectinload(OptimizationRun.decisions)).where(OptimizationRun.id == request.optimization_run_id))
    if not run:
        raise HTTPException(404, "Optimisation run not found")
    try:
        return run_simulation(db, run, trials=request.trials, seed=request.seed,
                              delay_probability=request.delay_probability,
                              late_penalty_per_unit=request.late_penalty_per_unit,
                              shipping_cost_multiplier=request.shipping_cost_multiplier)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
