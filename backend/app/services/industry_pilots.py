"""Bounded public-demo assignment MILP pilots with explicit parameter provenance.

NOT production models and NOT empirical crop-response / latency models. The optimizer
finds the global optimum of the supplied finite MILP, not of a real business.
All inputs are nonconfidential demonstration assumptions and never persisted.
"""
from __future__ import annotations

import csv
import io
import math
from collections import defaultdict
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from scipy.optimize import Bounds, LinearConstraint, milp

IndustryId = Literal["logistics", "agriculture", "technology"]
ObjectiveId = Literal["minimize_cost", "maximize_margin"]

RESOURCES = {
    "logistics": ("handling_units", "express_slots"),
    "agriculture": ("water_ml", "budget_aud"),
    "technology": ("cpu_units", "region_a_slots"),
}


class Option(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_id: str = Field(min_length=1, max_length=60, pattern=r"^[a-zA-Z0-9_.-]+$")
    option_id: str = Field(min_length=1, max_length=60, pattern=r"^[a-zA-Z0-9_.-]+$")
    objective_value: float = Field(ge=0, le=1_000_000)
    resources: dict[str, float] = Field(default_factory=dict, max_length=3)

    @model_validator(mode="after")
    def finite_resource_values(self):
        if any(not math.isfinite(v) or v < 0 or v > 1_000_000 for v in self.resources.values()):
            raise ValueError("Resource coefficients must be finite, nonnegative and bounded")
        return self


class PilotSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    industry: IndustryId
    objective: ObjectiveId
    capacities: dict[str, float] = Field(min_length=1, max_length=3)
    options: list[Option] = Field(min_length=2, max_length=400)
    input_provenance: Literal["synthetic_demo", "user_supplied_unverified"] = "user_supplied_unverified"

    @model_validator(mode="after")
    def check_structure(self):
        required = "maximize_margin" if self.industry == "agriculture" else "minimize_cost"
        if self.objective != required:
            raise ValueError(f"{self.industry} pilot supports only {required}")
        allowed = set(RESOURCES[self.industry])
        if set(self.capacities) != allowed:
            raise ValueError(f"Capacities must contain exactly: {', '.join(RESOURCES[self.industry])}")
        if any(not math.isfinite(v) or v < 0 or v > 1_000_000 for v in self.capacities.values()):
            raise ValueError("Capacities must be nonnegative finite quantities")
        options_by_item: dict[str, set[str]] = defaultdict(set)
        for o in self.options:
            if not set(o.resources).issubset(allowed):
                raise ValueError("Unexpected resource in option")
            if o.option_id in options_by_item[o.item_id]:
                raise ValueError("Duplicate item/option pair")
            options_by_item[o.item_id].add(o.option_id)
        if len(options_by_item) > 80:
            raise ValueError("Maximum 80 items")
        return self


# These costs, margins, water/CPU requirements and capacities are HYPOTHETICAL.
# No measurements have been copied from public dataset providers.
PRESETS: dict[str, dict] = {
    "logistics": {
        "industry": "logistics", "objective": "minimize_cost", "input_provenance": "synthetic_demo",
        "capacities": {"handling_units": 9, "express_slots": 2},
        "options": [
            {"item_id": "order_101", "option_id": "economy", "objective_value": 12, "resources": {"handling_units": 3}},
            {"item_id": "order_101", "option_id": "express", "objective_value": 20, "resources": {"handling_units": 2, "express_slots": 1}},
            {"item_id": "order_102", "option_id": "economy", "objective_value": 15, "resources": {"handling_units": 4}},
            {"item_id": "order_102", "option_id": "express", "objective_value": 22, "resources": {"handling_units": 2, "express_slots": 1}},
            {"item_id": "order_103", "option_id": "economy", "objective_value": 17, "resources": {"handling_units": 4}},
            {"item_id": "order_103", "option_id": "express", "objective_value": 25, "resources": {"handling_units": 2, "express_slots": 1}},
        ],
    },
    "agriculture": {
        "industry": "agriculture", "objective": "maximize_margin", "input_provenance": "synthetic_demo",
        "capacities": {"water_ml": 13, "budget_aud": 1300},
        "options": [
            {"item_id": "field_north", "option_id": "wheat", "objective_value": 700, "resources": {"water_ml": 6, "budget_aud": 500}},
            {"item_id": "field_north", "option_id": "barley", "objective_value": 510, "resources": {"water_ml": 3, "budget_aud": 350}},
            {"item_id": "field_east", "option_id": "wheat", "objective_value": 650, "resources": {"water_ml": 7, "budget_aud": 600}},
            {"item_id": "field_east", "option_id": "barley", "objective_value": 470, "resources": {"water_ml": 3, "budget_aud": 350}},
            {"item_id": "field_west", "option_id": "wheat", "objective_value": 600, "resources": {"water_ml": 6, "budget_aud": 540}},
            {"item_id": "field_west", "option_id": "barley", "objective_value": 400, "resources": {"water_ml": 2, "budget_aud": 300}},
        ],
    },
    "technology": {
        "industry": "technology", "objective": "minimize_cost", "input_provenance": "synthetic_demo",
        "capacities": {"cpu_units": 13, "region_a_slots": 2},
        "options": [
            {"item_id": "service_api", "option_id": "region_a", "objective_value": 210, "resources": {"cpu_units": 4, "region_a_slots": 1}},
            {"item_id": "service_api", "option_id": "region_b", "objective_value": 245, "resources": {"cpu_units": 3}},
            {"item_id": "service_search", "option_id": "region_a", "objective_value": 180, "resources": {"cpu_units": 5, "region_a_slots": 1}},
            {"item_id": "service_search", "option_id": "region_b", "objective_value": 230, "resources": {"cpu_units": 4}},
            {"item_id": "service_worker", "option_id": "region_a", "objective_value": 160, "resources": {"cpu_units": 5, "region_a_slots": 1}},
            {"item_id": "service_worker", "option_id": "region_b", "objective_value": 190, "resources": {"cpu_units": 3}},
        ],
    },
}


DATA_SOURCES = [
    {"industry": "logistics", "name": "UCI Online Retail II", "url": "https://archive.ics.uci.edu/dataset/502/online+retail+ii", "license": "CC BY 4.0", "use": "Historical transaction and SKU demand exploration", "missing": "Handling times, shipping costs, inventory, supply constraints"},
    {"industry": "agriculture", "name": "ABARES Australian Crop Report", "url": "https://www.agriculture.gov.au/abares/research-topics/agricultural-outlook/australian-crop-report", "license": "Review applicable Australian Government dataset terms", "use": "Regional crop area, yield and production context", "missing": "Field-specific yield response, water requirements, gross margin and input prices"},
    {"industry": "technology", "name": "Google Borg cluster traces", "url": "https://github.com/google/cluster-data", "license": "CC BY (see source)", "use": "Historical workload demand and resource utilisation", "missing": "Cloud prices, geographic restrictions, latency/SLA response and service placement policy"},
]


def solve_pilot(spec: PilotSpec) -> dict:
    """Solve a small 0/1 assignment MILP and independently verify its solution."""
    items = sorted({o.item_id for o in spec.options})
    n = len(spec.options)
    rkeys = RESOURCES[spec.industry]
    rows = []
    lower = []
    upper = []
    for item in items:
        rows.append([1.0 if o.item_id == item else 0.0 for o in spec.options])
        lower.append(1.0)
        upper.append(1.0)
    for resource in rkeys:
        rows.append([o.resources.get(resource, 0.0) for o in spec.options])
        lower.append(0.0)
        upper.append(spec.capacities[resource])
    values = np.array([o.objective_value for o in spec.options], dtype=float)
    sign = -1 if spec.objective == "maximize_margin" else 1
    constraints = LinearConstraint(np.array(rows), np.array(lower), np.array(upper))
    result = milp(sign * values, integrality=np.ones(n), bounds=Bounds(np.zeros(n), np.ones(n)), constraints=constraints, options={"time_limit": 8.0, "mip_rel_gap": 0.0})
    if result.x is None or result.status != 0:
        return {"industry": spec.industry, "status": "infeasible" if result.status == 2 else "not_proven_optimal", "solver_status_code": int(result.status), "message": "No certified optimum was obtained. Review capacities, options or the solver status.", "input_provenance": spec.input_provenance, "decisions": [], "objective_value": None, "constraint_usage": {}}
    x = np.asarray(result.x)
    chosen = np.where(x > 0.5)[0]
    usage = {r: float(sum(spec.options[i].resources.get(r, 0) for i in chosen)) for r in rkeys}
    assignments = [spec.options[i] for i in chosen]
    valid = (len(assignments) == len(items) and len({o.item_id for o in assignments}) == len(items)
             and all(usage[k] <= spec.capacities[k] + 1e-6 for k in rkeys)
             and np.max(np.abs(x - np.rint(x))) < 1e-6)
    if not valid:
        raise RuntimeError("Solver solution failed independent feasibility verification")
    return {"industry": spec.industry, "objective": spec.objective, "status": "optimal", "solver_status_code": int(result.status), "message": "Globally optimal only for this specified finite synthetic/unverified-input MILP", "objective_value": round(float(sum(o.objective_value for o in assignments)), 4), "decisions": [{"item_id": o.item_id, "option_id": o.option_id, "contribution": o.objective_value} for o in assignments], "constraint_usage": {k: {"used": round(usage[k], 5), "limit": spec.capacities[k]} for k in rkeys}, "item_count": len(items), "input_provenance": spec.input_provenance, "assumptions": ["Every item selects exactly one option", "All resource coefficients, costs and margins are user-provided or hypothetical", "Options encode assumed eligibility, not learned causal or performance responses", "Nothing is executed against external systems or stored"]}


def parse_csv_scenario(industry: IndustryId, csv_text: str, capacities: dict[str, float]) -> PilotSpec:
    """Parse a tiny, bounded non-confidential decision-options CSV, not raw business data."""
    if len(csv_text.encode("utf-8")) > 100_000 or "\x00" in csv_text:
        raise ValueError("CSV must be <=100KB and contain no NUL bytes")
    reader = csv.DictReader(io.StringIO(csv_text, newline=""), strict=True)
    allowed = {"item_id", "option_id", "objective_value", *RESOURCES[industry]}
    if not reader.fieldnames or set(reader.fieldnames) != allowed or len(reader.fieldnames) != len(allowed):
        raise ValueError("CSV columns must exactly match the selected pilot schema")
    options = []
    try:
        for row in reader:
            if len(options) >= 400:
                raise ValueError("Maximum 400 option rows")
            options.append(Option(item_id=row["item_id"], option_id=row["option_id"], objective_value=float(row["objective_value"]), resources={k: float(row[k]) for k in RESOURCES[industry]}))
    except (csv.Error, TypeError, KeyError, OverflowError) as exc:
        raise ValueError("Malformed CSV") from exc
    return PilotSpec(industry=industry, objective="maximize_margin" if industry == "agriculture" else "minimize_cost", capacities=capacities, options=options, input_provenance="user_supplied_unverified")
