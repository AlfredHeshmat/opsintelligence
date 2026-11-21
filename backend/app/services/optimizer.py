"""Binary MILP: each order is deferred, economy shipped, or express shipped.

Costs are transparent demo assumptions, not guarantees of realised savings.
"""
from datetime import datetime, timezone
from decimal import Decimal
from math import ceil
from sqlalchemy import select
from sqlalchemy.orm import Session
from scipy.optimize import Bounds, LinearConstraint, milp
import numpy as np
from app.models import Capacity, Inventory, Order, OptimizationDecision, OptimizationRun, ShippingOption

UNITS_PER_LABOUR_HOUR = 8
DEFER_PENALTY_PER_UNIT = 12
LATE_PENALTY_PER_PRIORITY = 16

def solve_allocation(db: Session, handling_capacity: int | None = None, labour_hours: int | None = None):
    orders=db.scalars(select(Order).where(Order.status=='pending').order_by(Order.id)).all()
    capacity=db.scalars(select(Capacity).order_by(Capacity.date.desc())).first()
    options=db.scalars(select(ShippingOption).order_by(ShippingOption.transit_days.desc())).all()
    inv={x.sku:max(0,x.available_quantity-x.reserved_quantity) for x in db.scalars(select(Inventory)).all()}
    if not orders or not capacity or len(options)<2:
        raise ValueError('No pending orders, capacity, or shipping options: seed data first')
    handling=handling_capacity if handling_capacity is not None else capacity.handling_units
    labour=labour_hours if labour_hours is not None else capacity.labour_hours
    if handling<0 or labour<0: raise ValueError('Capacity cannot be negative')
    # Bound total computation for a responsive portfolio demo.
    if len(orders)>700: raise ValueError('Too many pending orders for interactive solve (limit 700)')
    n=len(orders)
    # Variables: x[i,0] defer, x[i,1] economy, x[i,2] express.
    choices=[None,options[0],options[-1]]
    c=[]
    for order in orders:
        for choice in choices:
            if choice is None:
                cost=order.quantity*DEFER_PENALTY_PER_UNIT*order.priority
            else:
                days_left=(order.promised_at.replace(tzinfo=timezone.utc) if order.promised_at.tzinfo is None else order.promised_at).date() - datetime.now(timezone.utc).date()
                late=max(0,choice.transit_days-days_left.days)
                cost=float(choice.cost_per_order)+late*LATE_PENALTY_PER_PRIORITY*order.priority
            c.append(float(cost))
    constraints=[]
    # Exactly one action for each order.
    matrix=np.zeros((n,3*n))
    for i in range(n): matrix[i,3*i:3*i+3]=1
    constraints.append(LinearConstraint(matrix,np.ones(n),np.ones(n)))
    used_units=np.zeros(3*n)
    for i,o in enumerate(orders): used_units[3*i+1:3*i+3]=o.quantity
    constraints.append(LinearConstraint(used_units,-np.inf,min(handling,labour*UNITS_PER_LABOUR_HOUR)))
    for sku,qty in inv.items():
        row=np.zeros(3*n)
        for i,o in enumerate(orders):
            if o.sku==sku: row[3*i+1:3*i+3]=o.quantity
        constraints.append(LinearConstraint(row,-np.inf,qty))
    result=milp(c=np.array(c),integrality=np.ones(3*n),bounds=Bounds(0,1),constraints=constraints,options={'time_limit':12,'mip_rel_gap':0.001})
    states={0:'optimal',1:'limit_reached',2:'infeasible',3:'unbounded',4:'solver_error'}
    status=states.get(result.status,'unknown')
    baseline=sum(c[3*i] for i in range(n))
    run=OptimizationRun(status=status,objective_value=Decimal(str(round(result.fun,2))) if result.fun is not None else None,
                        baseline_cost=Decimal(str(round(baseline,2))),handling_capacity=handling,labour_capacity_hours=labour,
                        solver_message=str(result.message)[:400])
    db.add(run)
    if result.x is not None:
        for i,o in enumerate(orders):
            position=int(np.argmax(result.x[3*i:3*i+3]))
            option=choices[position]
            run.decisions.append(OptimizationDecision(order_id=o.id, action='defer' if option is None else 'ship',
                                 shipping_option=option.name if option else None,estimated_cost=Decimal(str(round(c[3*i+position],2)))))
    db.commit()
    db.refresh(run)
    return run

def serialize_run(run: OptimizationRun):
    return {'id':run.id,'status':run.status,'solver_message':run.solver_message,
            'objective_value':float(run.objective_value) if run.objective_value is not None else None,
            'baseline_cost':float(run.baseline_cost) if run.baseline_cost is not None else None,
            'estimated_savings':round(float(run.baseline_cost-run.objective_value),2) if run.objective_value is not None else None,
            'handling_capacity':run.handling_capacity,'labour_capacity_hours':run.labour_capacity_hours,
            'synthetic':True,'decisions':[{'order_id':d.order_id,'action':d.action,'shipping_option':d.shipping_option,
                                           'estimated_cost':float(d.estimated_cost)} for d in run.decisions]}
