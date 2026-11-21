from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # noqa: F401
from app.services.demo import seed_demo
from app.services.optimizer import solve_allocation
from app.services.prediction import train_model, predict_pending
from app.services.product_analytics import product_performance
from app.services.simulation import run_simulation


@pytest.fixture
def db():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_demo(session, count=240, seed=42)
        yield session
    engine.dispose()


def test_product_metrics_reconcile(db):
    report = product_performance(db, days=30)
    assert sum(p['orders'] for p in report['products']) == report['totals']['orders']
    assert sum(p['units'] for p in report['products']) == report['totals']['units']
    sku_report = product_performance(db, days=7, sku='SKU-A')
    assert all(p['sku'] == 'SKU-A' for p in sku_report['products'])
    with pytest.raises(ValueError):
        product_performance(db, days=31)


def test_model_is_trained_and_risk_is_bounded(db, tmp_path):
    model_path = tmp_path / 'model.joblib'
    report = train_model(db, model_path=model_path)
    assert report['trained_on'] > report['tested_on'] > 0
    assert 0 <= report['accuracy'] <= 1
    assert report['synthetic'] is True
    result = predict_pending(db, model_path=model_path, sku='SKU-B')
    assert result['predictions']
    assert all(0 <= r['delay_probability'] <= 1 and r['sku'] == 'SKU-B' for r in result['predictions'])


def test_simulation_is_reproducible_and_sensitive(db):
    run = solve_allocation(db, handling_capacity=90, labour_hours=28)
    a = run_simulation(db, run, trials=300, seed=123, delay_probability=0.1)
    b = run_simulation(db, run, trials=300, seed=123, delay_probability=0.1)
    c = run_simulation(db, run, trials=300, seed=123, delay_probability=0.95)
    assert a == b
    assert a['results']['expected_plan_cost'] <= c['results']['expected_plan_cost']
    assert 0 <= a['results']['probability_below_baseline'] <= 1
    with pytest.raises(ValueError):
        run_simulation(db, run, trials=10)
