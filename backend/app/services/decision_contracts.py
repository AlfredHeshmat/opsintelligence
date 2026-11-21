"""Shared, validated decision specifications; validation does not execute a solver."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.industry_registry import REGISTRY_VERSION, get_industry


class ConstraintSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metric_id: str = Field(min_length=1, max_length=64)
    operator: Literal["<=", ">=", "=="]
    value: float = Field(allow_inf_nan=False)
    unit: str = Field(min_length=1, max_length=32)
    mandatory: bool = True


class DecisionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    industry: str = Field(min_length=1, max_length=64)
    subindustry: str = Field(min_length=1, max_length=64)
    objective: str = Field(min_length=1, max_length=64)
    horizon_months: int = Field(default=12, ge=1, le=60)
    risk_appetite: Literal["conservative", "balanced", "aggressive"] = "balanced"
    constraints: list[ConstraintSpec] = Field(default_factory=list, max_length=100)
    data_source: Literal["synthetic", "validated_company_data"] = "synthetic"

    @model_validator(mode="after")
    def validate_model(self):
        industry = get_industry(self.industry)
        if industry is None:
            raise ValueError("Unrecognised industry. Select a registered industry.")
        if self.subindustry not in industry.subindustries:
            raise ValueError("Subindustry is not registered for this industry.")
        if self.objective not in industry.objectives:
            raise ValueError("Objective is not supported by this industry definition.")
        names = [c.metric_id for c in self.constraints]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate constraint metric IDs are ambiguous.")
        return self


def inspect_decision(spec: DecisionSpec) -> dict:
    industry = get_industry(spec.industry)
    assert industry is not None  # Pydantic validation establishes this
    metric_units = {m.id: m.unit for m in industry.metrics}
    known_constraint_units = {
        "capex_reduction_percent": "percent", "capital_budget": "AUD",
        "handling_capacity": "units", "labour_hours": "hours",
        "water_allocation": "ML", "land_area": "ha", "budget": "AUD",
        "latency_sla": "ms", "availability_sla": "percent",
        "inventory_available": "units", "labour_hours": "hours",
        "shipping_eligibility": "boolean", "handling_capacity": "units",
        "region_capacity": "instances", "data_residency": "boolean",
        "soil_suitability": "index", "environmental_limits": "index",
    }
    errors: list[str] = []
    for c in spec.constraints:
        expected = known_constraint_units.get(c.metric_id) or metric_units.get(c.metric_id)
        if c.metric_id not in industry.constraints and c.metric_id not in metric_units and c.metric_id != "capex_reduction_percent":
            errors.append(f"Unsupported constraint '{c.metric_id}' for {spec.industry}")
        elif expected is not None and expected != "industry_defined" and c.unit != expected:
            errors.append(f"Incorrect unit for {c.metric_id}: expected {expected}, received {c.unit}")
        if c.metric_id == "capex_reduction_percent" and not 0 <= c.value <= 100:
            errors.append("CAPEX reduction must be between 0 and 100 percent")
    valid = len(errors) == 0
    return {
        "registry_version": REGISTRY_VERSION,
        "industry": spec.industry,
        "subindustry": spec.subindustry,
        "objective": spec.objective,
        "specification_valid": valid,
        "errors": errors,
        "support_level": industry.support_level,
        "adapter_id": industry.adapter_id,
        "required_fields": list(industry.required_fields),
        "solver_executable_for_this_spec": False,
        "decision_status": "contract_validated_not_solved" if valid else "invalid_specification",
        "reason": "Adapter capability is catalogue metadata only. This endpoint never executes a solver or accesses company data.",
    }
