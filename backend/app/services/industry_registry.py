"""Versioned industry definitions. This is a catalogue, not a collection of solvers.

Every metric has an explicit unit and aggregation meaning. Industry templates carry
capability evidence so clients cannot confuse model discovery with implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SupportLevel = Literal["catalogue_only", "data_contract_defined", "solver_demo", "validated"]


@dataclass(frozen=True)
class Metric:
    id: str
    label: str
    unit: str
    description: str
    aggregation: str = "none"

    def to_dict(self) -> dict:
        return vars(self).copy()


@dataclass(frozen=True)
class Industry:
    id: str
    name: str
    subindustries: tuple[str, ...]
    metrics: tuple[Metric, ...]
    objectives: tuple[str, ...]
    constraints: tuple[str, ...]
    required_fields: tuple[str, ...]
    support_level: SupportLevel = "catalogue_only"
    adapter_id: str | None = None
    illustrative_scenario: str = ""
    model_warning: str = "No validated optimisation adapter is available for this industry."

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "subindustries": list(self.subindustries),
            "metrics": [m.to_dict() for m in self.metrics],
            "objectives": list(self.objectives),
            "constraints": list(self.constraints),
            "required_fields": list(self.required_fields),
            "support_level": self.support_level,
            "adapter_id": self.adapter_id,
            "solver_available": self.support_level in ("solver_demo", "validated"),
            "illustrative_scenario": self.illustrative_scenario,
            "model_warning": self.model_warning,
        }


def metric(id: str, unit: str, description: str, aggregation: str = "none") -> Metric:
    return Metric(id=id, label=id.replace("_", " ").title(), unit=unit, description=description, aggregation=aggregation)


REGISTRY_VERSION = "4a.1"
REGISTRY: dict[str, Industry] = {
    "logistics": Industry(
        "logistics", "Logistics & Warehousing", ("warehouse", "last_mile", "freight", "distribution"),
        (metric("fulfilment_rate", "percent", "Delivered orders divided by eligible orders"),
         metric("delivery_cost", "AUD", "Modelled shipping and fulfilment cost", "sum"),
         metric("backlog", "orders", "Orders not yet fulfilled", "sum"),
         metric("inventory_turnover", "ratio", "Period stock throughput divided by average stock")),
        ("minimize_cost", "maximize_service"),
        ("inventory_available", "labour_hours", "handling_capacity", "shipping_eligibility"),
        ("order_id", "sku", "quantity", "priority", "shipping_cost", "inventory_available", "handling_capacity", "labour_hours"),
        "solver_demo", "warehouse_milp_v1",
        "Allocate pending orders to economy, express, or defer under resource constraints.",
        "Warehouse MILP is demonstrated on synthetic data; it does not solve arbitrary logistics problems.",
    ),
    "technology": Industry(
        "technology", "Technology & Software", ("saas", "cloud_infrastructure", "ai_compute", "it_services", "cybersecurity", "telecom"),
        (metric("cloud_spend", "AUD/month", "Billed infrastructure expenditure", "sum"),
         metric("p95_latency", "ms", "95th percentile application response latency"),
         metric("availability", "percent", "Service availability over the reporting period"),
         metric("gross_margin", "percent", "Gross profit divided by revenue")),
        ("minimize_cost", "maximize_margin", "maximize_service", "minimize_risk"),
        ("latency_sla", "availability_sla", "region_capacity", "data_residency", "budget"),
        ("service_id", "workload_demand", "region", "compute_capacity", "unit_cost", "p95_latency", "availability"),
        "data_contract_defined", None,
        "Reduce cloud expenditure while respecting availability, latency and region restrictions.",
        "No cloud-capacity solver or workload-performance response model has been implemented.",
    ),
    "agriculture": Industry(
        "agriculture", "Agriculture & AgriTech", ("crop_production", "precision_agriculture", "irrigation", "livestock", "agri_supply_chain"),
        (metric("yield_tonnes_per_ha", "t/ha", "Harvest yield per cultivated hectare"),
         metric("water_use", "ML", "Water used over the reporting period", "sum"),
         metric("gross_margin", "AUD/ha", "Agricultural gross margin per hectare"),
         metric("ndvi", "index", "Vegetation index derived from remote sensing")),
        ("maximize_margin", "minimize_cost", "minimize_risk", "maximize_yield"),
        ("water_allocation", "land_area", "budget", "soil_suitability", "environmental_limits"),
        ("field_id", "crop", "area_ha", "soil_type", "rainfall_mm", "forecast_yield_t_ha", "input_cost_aud"),
        "data_contract_defined", None,
        "Choose crop and resource allocations under water, weather, land, and budget limits.",
        "Yield forecasting alone is not an intervention model: fertiliser or irrigation response requires independent validation.",
    ),
}

# Catalog breadth is intentionally metadata-only until an expert-reviewed domain
# decision model and executable regression tests are registered.
EXTRA_INDUSTRIES = (
    ("airline", "Airlines & Aviation", ("passenger", "cargo", "airports"), ("fuel_cost", "on_time_performance"), ("minimize_cost", "maximize_margin"), "Fuel and weather-aware schedule planning"),
    ("mining", "Mining & Resources", ("surface_mining", "underground", "minerals"), ("unit_production_cost", "equipment_utilization"), ("minimize_cost", "maximize_margin"), "Mine production and equipment scheduling"),
    ("food", "Food & Beverage", ("restaurants", "food_manufacturing", "catering"), ("waste_rate", "food_cost"), ("minimize_cost", "maximize_margin"), "Inventory and spoilage optimisation"),
    ("healthcare", "Healthcare", ("hospitals", "clinics", "aged_care"), ("wait_time", "capacity"), ("maximize_service", "minimize_cost"), "Safe workforce and bed allocation"),
    ("finance", "Banking & Finance", ("banking", "investment", "payments"), ("risk_adjusted_return", "liquidity"), ("maximize_margin", "minimize_risk"), "Risk-constrained asset allocation"),
    ("consulting", "Consulting & Professional Services", ("strategy", "engineering", "it_consulting"), ("project_margin", "billable_utilization"), ("maximize_margin", "minimize_cost"), "Skills-aware project staffing"),
    ("manufacturing", "Manufacturing", ("discrete", "process", "industrial"), ("throughput", "downtime"), ("maximize_margin", "minimize_cost"), "Production allocation and maintenance"),
    ("energy", "Energy & Utilities", ("power_generation", "grid", "water_utilities"), ("dispatch_cost", "reliability"), ("minimize_cost", "maximize_service"), "Demand and generation dispatch"),
    ("retail", "Retail & E-commerce", ("physical_retail", "ecommerce", "wholesale"), ("sales_margin", "stockout_rate"), ("maximize_margin", "minimize_cost"), "Assortment and inventory planning"),
    ("construction", "Construction", ("commercial", "residential", "civil"), ("project_cost", "schedule_delay"), ("minimize_cost", "minimize_risk"), "Equipment and project scheduling"),
    ("telecommunications", "Telecommunications", ("mobile", "broadband", "network"), ("network_latency", "availability"), ("minimize_cost", "maximize_service"), "Network capacity placement"),
    ("hospitality", "Hospitality & Tourism", ("hotels", "tourism", "events"), ("occupancy_rate", "revenue_per_room"), ("maximize_margin", "maximize_service"), "Occupancy and staffing planning"),
    ("education", "Education", ("schools", "higher_education", "training"), ("seat_utilization", "student_wait_time"), ("maximize_service", "minimize_cost"), "Timetable and course capacity"),
    ("real_estate", "Real Estate", ("commercial", "residential", "property_management"), ("occupancy_rate", "maintenance_cost"), ("maximize_margin", "minimize_cost"), "Portfolio maintenance planning"),
    ("insurance", "Insurance", ("general", "life", "reinsurance"), ("claims_cost", "capital_reserve"), ("minimize_risk", "minimize_cost"), "Risk-aware capital allocation"),
    ("maritime", "Maritime & Ports", ("ports", "shipping", "terminals"), ("berth_utilization", "vessel_delay"), ("minimize_cost", "maximize_service"), "Berth and cargo scheduling"),
    ("environment", "Waste & Environmental Services", ("waste", "recycling", "environmental"), ("collection_cost", "recycling_rate"), ("minimize_cost", "maximize_service"), "Collection and recovery planning"),
)
for _key, _name, _sub, _metrics, _goals, _scenario in EXTRA_INDUSTRIES:
    REGISTRY[_key] = Industry(
        _key, _name, _sub,
        tuple(metric(m, "industry_defined", "Metric definition requires a validated industry data contract") for m in _metrics),
        _goals, (), (), "catalogue_only", None, _scenario,
    )


def get_industry(industry_id: str) -> Industry | None:
    return REGISTRY.get(industry_id)


def registry_summary() -> dict:
    return {"registry_version": REGISTRY_VERSION,
            "industries": [industry.to_dict() for industry in REGISTRY.values()],
            "disclaimer": "Catalogue inclusion does not mean a solver, data connector or validated model exists."}
