"""Opt-in PUBLIC demo endpoints. Never send confidential datasets to these routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict, ValidationError

from app.services.industry_pilots import (
    DATA_SOURCES, PRESETS, IndustryId, PilotSpec, RESOURCES,
    parse_csv_scenario, solve_pilot,
)

router = APIRouter(prefix="/api/v1/industry-pilots", tags=["public-synthetic-industry-pilots"])


@router.get("/catalogue")
def catalogue():
    return {"resources": RESOURCES, "data_sources": DATA_SOURCES, "preset_industries": list(PRESETS), "data_policy": "Nonconfidential demonstration only. Public data sources are research references, not ingested datasets.", "solvers": "Three small assignment MILP pilots; NOT production industry optimisers"}


@router.get("/presets/{industry}")
def preset(industry: IndustryId):
    return {"scenario": PRESETS[industry], "warning": "All optimisation coefficients are synthetic assumptions, NOT measured public dataset values."}


@router.post("/solve")
def solve(spec: PilotSpec):
    return solve_pilot(spec)


class CSVCase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    industry: IndustryId
    capacities: dict[str, float]
    csv_text: str = Field(min_length=1, max_length=100_000)


@router.post("/solve-csv")
def solve_csv(payload: CSVCase):
    try:
        spec = parse_csv_scenario(payload.industry, payload.csv_text, payload.capacities)
    except (ValueError, TypeError, ValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return solve_pilot(spec)
