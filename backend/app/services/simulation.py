"""Transparent probabilistic comparison of an already-computed allocation vs defer-all.

The random late-delivery shocks are *assumptions*, not calibrated forecasts.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Sequence

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import OptimizationRun, Order
from app.services.optimizer import serialize_run


def run_simulation(db: Session, run: OptimizationRun, *, trials: int = 1000,
                   seed: int = 42, delay_probability: float = 0.20,
                   late_penalty_per_unit: float = 8.0, shipping_cost_multiplier: float = 1.0) -> dict:
    if run.status != "optimal" or run.objective_value is None:
        raise ValueError("A proven-optimal allocation run is required for comparison")
    if not 100 <= trials <= 5000:
        raise ValueError("trials must be 100..5000")
    if not 0 <= delay_probability <= 1 or late_penalty_per_unit < 0 or shipping_cost_multiplier < 0:
        raise ValueError("Invalid simulation assumptions")
    decisions = serialize_run(run)["decisions"]
    order_ids = [d["order_id"] for d in decisions]
    orders = {o.id: o for o in db.scalars(select(Order).where(Order.id.in_(order_ids))).all()}
    if len(orders) != len(decisions):
        raise ValueError("Some orders in the saved allocation are missing")
    # Baseline is always defer-all. Shipment decisions incur stochastic extra penalties.
    baseline_cost = float(run.baseline_cost)
    rng = np.random.default_rng(seed)
    shipping_decisions = [d for d in decisions if d["action"] == "ship"]
    defer_cost = sum(d["estimated_cost"] for d in decisions if d["action"] == "defer")
    shipping_base = sum(d["estimated_cost"] for d in shipping_decisions)
    # Shipping cost multiplier acts on the entire modelled shipping-decision cost,
    # including any deterministic late penalty: this is a scenario sensitivity, not an actual carrier tariff.
    fixed_cost = defer_cost + shipping_base * shipping_cost_multiplier
    penalty_vector = np.array([orders[d["order_id"]].quantity * late_penalty_per_unit for d in shipping_decisions], dtype=float)
    if len(penalty_vector):
        late_shocks = rng.binomial(1, delay_probability, size=(trials, len(penalty_vector)))
        scenario_costs = fixed_cost + late_shocks @ penalty_vector
    else:
        scenario_costs = np.full(trials, fixed_cost)
    savings = baseline_cost - scenario_costs
    return {
        "synthetic": True, "run_id": run.id,
        "baseline_description": "Defer every pending order; deterministic modelled penalty",
        "baseline_cost": round(baseline_cost, 2),
        "assumptions": {"trials": trials, "seed": seed,
                        "delay_probability": delay_probability,
                        "late_penalty_per_unit": late_penalty_per_unit,
                        "shipping_cost_multiplier": shipping_cost_multiplier},
        "results": {"expected_plan_cost": round(float(np.mean(scenario_costs)), 2),
                    "plan_cost_p10": round(float(np.quantile(scenario_costs, .10)), 2),
                    "plan_cost_p90": round(float(np.quantile(scenario_costs, .90)), 2),
                    "expected_improvement": round(float(np.mean(savings)), 2),
                    "improvement_p10": round(float(np.quantile(savings, .10)), 2),
                    "improvement_p90": round(float(np.quantile(savings, .90)), 2),
                    "probability_below_baseline": round(float(np.mean(scenario_costs < baseline_cost)), 4)},
        "limitations": "Independent Bernoulli delay shocks at user-selected rates; illustrative scenario, not validated savings or an operational forecast.",
    }
