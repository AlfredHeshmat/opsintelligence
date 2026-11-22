"""Bounded, reproducible logistics MILP over imported *pending* project orders.

A planning comparison, not a claim of financial savings or operational feasibility.
"""
from decimal import Decimal
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

MODEL_VERSION = 'project-dispatch-knapsack-v1'
MAX_PENDING = 150
PRIORITY_WEIGHTS = {'standard': 1, 'priority': 2, 'express': 3}


def plan_dispatch(orders, handling_capacity: int, defer_penalty_aud_per_unit: Decimal):
    """Minimise shipping estimate + penalty on deferred units under a global unit limit.

    One binary decision per pending order. Penalty weights are *assumptions*, not
    derived from historical losses. Unshipped and cancelled orders are excluded.
    """
    if not (0 <= handling_capacity <= 1_000_000):
        raise ValueError('Handling capacity must be between 0 and 1,000,000 units')
    if not (Decimal('0.01') <= defer_penalty_aud_per_unit <= Decimal('1000')):
        raise ValueError('Defer penalty must be between $0.01 and $1,000 per unit')
    pending = sorted((o for o in orders if o.status == 'pending'), key=lambda o: o.order_id)
    if not pending:
        raise ValueError('No pending orders in the selected project dataset')
    if len(pending) > MAX_PENDING:
        raise ValueError(f'This interactive solver supports at most {MAX_PENDING} pending orders')
    quantities = np.array([o.quantity for o in pending], dtype=float)
    defer_cents = [int((defer_penalty_aud_per_unit * o.quantity * PRIORITY_WEIGHTS[o.priority] * 100).to_integral_value()) for o in pending]
    ship_cents = [int((o.shipping_cost_aud * 100).to_integral_value()) for o in pending]
    # Variable x_i=1 dispatch, x_i=0 defer. All costs integer cents.
    costs = np.array([s - d for s, d in zip(ship_cents, defer_cents)], dtype=float)
    result = milp(c=costs, integrality=np.ones(len(pending)),
                  bounds=Bounds(np.zeros(len(pending)), np.ones(len(pending))),
                  constraints=[LinearConstraint(quantities, -np.inf, handling_capacity)],
                  options={'time_limit': 8, 'mip_rel_gap': 0.0})
    statuses = {0: 'optimal', 1: 'limit_reached', 2: 'infeasible', 3: 'unbounded', 4: 'solver_error'}
    status = statuses.get(result.status, 'solver_error')
    baseline = Decimal(sum(defer_cents)) / 100
    # NEVER present an incumbent as proven optimal after a time limit.
    if status != 'optimal' or result.x is None:
        return {'status': status, 'solver_message': str(result.message)[:300],
                'baseline_cost_aud': baseline, 'objective_cost_aud': None,
                'decisions': [], 'pending_orders': len(pending)}
    selected = [int(round(float(x))) for x in result.x]
    if any(abs(x - round(x)) > 1e-5 for x in result.x) or sum(o.quantity * x for o, x in zip(pending, selected)) > handling_capacity:
        raise RuntimeError('Solver returned a decision violating the declared constraints')
    total_cents = sum(ship if chosen else defer for ship, defer, chosen in zip(ship_cents, defer_cents, selected))
    decisions = [{'order_id': o.order_id, 'sku': o.sku, 'warehouse_id': o.warehouse_id,
                  'units': o.quantity, 'priority': o.priority,
                  'action': 'dispatch' if chosen else 'defer',
                  'modelled_cost_aud': float(Decimal(ship if chosen else defer) / 100)}
                 for o, ship, defer, chosen in zip(pending, ship_cents, defer_cents, selected)]
    return {'status': status, 'solver_message': str(result.message)[:300],
            'baseline_cost_aud': baseline, 'objective_cost_aud': Decimal(total_cents) / 100,
            'decisions': decisions, 'pending_orders': len(pending)}
