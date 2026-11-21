"""Safe discovery and planning for a future multi-industry decision workspace.

No secrets are accepted, no external URLs are fetched and no optimisation is
claimed outside the validated warehouse model.
"""
from __future__ import annotations

import csv
import io
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/api/v1/workspace", tags=["decision-workspace"])

INDUSTRIES = {
    "logistics": {"name": "Logistics & Warehousing", "metrics": ["fulfilment_rate", "delivery_cost", "backlog", "inventory_turnover"], "objectives": ["minimize_cost", "maximize_service"], "status": "solver_available"},
    "airline": {"name": "Airlines & Aviation", "metrics": ["fuel_cost", "on_time_performance", "aircraft_utilization", "route_profitability"], "objectives": ["minimize_cost", "maximize_margin"], "status": "blueprint_only"},
    "mining": {"name": "Mining & Resources", "metrics": ["unit_production_cost", "equipment_utilization", "ore_recovery", "capex"], "objectives": ["minimize_cost", "maximize_margin"], "status": "blueprint_only"},
    "food": {"name": "Food & Beverage", "metrics": ["gross_margin", "waste_rate", "stockout_rate", "food_cost"], "objectives": ["minimize_cost", "maximize_margin"], "status": "blueprint_only"},
    "healthcare": {"name": "Healthcare", "metrics": ["capacity", "wait_time", "staff_utilization", "quality"], "objectives": ["maximize_service", "minimize_cost"], "status": "blueprint_only"},
    "finance": {"name": "Financial Services", "metrics": ["risk_adjusted_return", "liquidity", "drawdown", "capex"], "objectives": ["maximize_margin", "minimize_risk"], "status": "blueprint_only"},
    "consulting": {"name": "Consulting & Professional Services", "metrics": ["project_margin", "billable_utilization", "client_retention", "capex"], "objectives": ["maximize_margin", "minimize_cost"], "status": "blueprint_only"},
    "manufacturing": {"name": "Manufacturing", "metrics": ["throughput", "gross_margin", "downtime", "capex"], "objectives": ["maximize_margin", "minimize_cost"], "status": "blueprint_only"},
}

SYNONYMS = {
    "logistics": {"sku", "shipment", "carrier", "tracking", "warehouse", "promised_at"},
    "airline": {"flight", "aircraft", "airport", "fuel_burn", "departure", "arrival"},
    "mining": {"ore", "grade", "haul", "pit", "drill", "tonnage"},
    "food": {"ingredient", "recipe", "expiry", "menu", "waste", "batch"},
    "healthcare": {"patient", "admission", "bed", "ward", "clinician", "triage"},
    "finance": {"portfolio", "ticker", "asset", "nav", "exposure", "return"},
    "consulting": {"billable", "project", "timesheet", "consultant", "client", "engagement"},
    "manufacturing": {"machine", "production", "plant", "downtime", "bom", "throughput"},
}

@router.get("/industries")
def industry_catalog():
    return {"industries": [{"id": key, **value} for key, value in INDUSTRIES.items()],
            "note": "Only the logistics warehouse solver is executable. Other industries provide schemas and planning guidance, not calculated optima."}

class ScenarioSpec(BaseModel):
    industry: str
    objective: Literal["minimize_cost", "maximize_margin", "maximize_service", "minimize_risk"]
    capex_reduction_percent: float = Field(default=7, ge=0, le=50)
    horizon_months: int = Field(default=12, ge=1, le=60)
    risk_appetite: Literal["conservative", "balanced", "aggressive"] = "balanced"

@router.post("/scenario/validate")
def validate_scenario(spec: ScenarioSpec):
    template = INDUSTRIES.get(spec.industry)
    if template is None:
        raise HTTPException(status_code=422, detail="Unknown industry")
    if spec.objective not in template["objectives"]:
        raise HTTPException(status_code=422, detail="Objective not supported by this industry template")
    return {
        "industry": spec.industry, "objective": spec.objective,
        "parameters": spec.model_dump(exclude={"industry", "objective"}),
        "applicable_kpis": template["metrics"],
        "solver_available": template["status"] == "solver_available",
        "decision_status": "configuration_validated_not_solved",
        "required_inputs": ["company financial records", "operational constraints", "time-aligned historical data", "data ownership and consent"],
        "message": "Scenario saved in the browser only. No company-specific optimum has been computed. Connect and validate data before solving."
    }

class CSVPreviewRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=120)
    csv_text: str = Field(min_length=1, max_length=200_000)

    @field_validator("filename")
    @classmethod
    def only_csv(cls, value: str):
        if not value.lower().endswith(".csv"):
            raise ValueError("Only CSV input is supported")
        return value

@router.post("/data/preview")
def preview_csv(spec: CSVPreviewRequest):
    """Schema-only, nonpersistent preview; never return potentially sensitive rows."""
    if "\x00" in spec.csv_text:
        raise HTTPException(status_code=422, detail="Null bytes are not permitted")
    try:
        stream = io.StringIO(spec.csv_text, newline="")
        reader = csv.reader(stream, strict=True)
        headers = next(reader)
        if not 1 <= len(headers) <= 80:
            raise ValueError("Expected 1 to 80 columns")
        headers = [h.strip().lower() for h in headers]
        if any(not h or len(h) > 80 for h in headers) or len(headers) != len(set(headers)):
            raise ValueError("Column names must be unique, nonempty, and at most 80 characters")
        count = 0
        for row in reader:
            if len(row) != len(headers):
                raise ValueError("Inconsistent CSV column count")
            count += 1
            if count > 10_000:
                raise ValueError("Maximum 10,000 records for preview")
    except (csv.Error, ValueError, StopIteration) as error:
        raise HTTPException(status_code=422, detail=f"Invalid CSV structure: {error}") from error

    scores = {industry: len(set(headers) & terms) for industry, terms in SYNONYMS.items()}
    ranked = sorted(scores, key=lambda key: scores[key], reverse=True)
    best = ranked[0] if scores[ranked[0]] > 0 else None
    return {"filename": spec.filename, "rows": count, "columns": headers,
            "candidate_industry": best, "confidence": "heuristic_low" if best else "undetermined",
            "industry_confirmation_required": True, "persisted": False,
            "warnings": ["Headers and row count only; content was not saved", "Industry detection is a weak heuristic, not a verified classification", "Do not submit personal or confidential company data to an unauthorised environment"]}

@router.get("/connections/capabilities")
def connector_capabilities():
    return {"csv_schema_preview": "available_local_nonpersistent",
            "database_connector": "not_configured",
            "api_key_connector": "disabled_pending_auth_and_secret_vault",
            "mcp_connector": "disabled_pending_auth_approval_and_allowlisting",
            "security": ["No credentials are accepted by these demo endpoints", "External network requests are disabled", "Production deployment requires authentication, RBAC, tenant isolation, encryption and audit logs"]}
