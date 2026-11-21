from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.db.base import Base
import app.models  # noqa: F401
from app.models import OptimizationRun, Order
from app.services.demo import seed_demo
from app.services.analytics import overview, anomalies
from app.services.optimizer import solve_allocation, serialize_run


def test_seed_analytics_and_solver():
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seeded=seed_demo(db, count=80, seed=42)
        assert seeded['inserted_orders']==80
        dashboard=overview(db)
        assert dashboard['total_orders']==80
        assert dashboard['pending_orders']>0
        assert dashboard['pending_units']>0
        assert isinstance(anomalies(db),list)
        run=solve_allocation(db,handling_capacity=40,labour_hours=10)
        result=serialize_run(run)
        assert result['status']=='optimal'
        assert len(result['decisions'])==dashboard['pending_orders']
        shipped=[d['order_id'] for d in result['decisions'] if d['action']=='ship']
        orders=db.scalars(select(Order).where(Order.id.in_(shipped))).all()
        assert sum(o.quantity for o in orders)<=40
        assert result['objective_value']<=result['baseline_cost']+0.01
        assert db.get(OptimizationRun,run.id) is not None


def test_zero_handling_capacity_forces_deferral():
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed_demo(db,count=30)
        run=solve_allocation(db,handling_capacity=0,labour_hours=10)
        assert run.status=='optimal'
        assert all(d.action=='defer' for d in run.decisions)
