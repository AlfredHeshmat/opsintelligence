"""Leakage-conscious, local-only delay prediction for *synthetic demo* orders.

No enterprise predictive performance should be inferred from these model metrics.
"""
from __future__ import annotations

from collections import Counter
from datetime import timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Order

FEATURES = ["quantity", "priority", "lead_days", "weekday", "sku"]
NUMERIC = FEATURES[:-1]
MODEL_PATH = Path(__file__).resolve().parents[2] / ".model_artifacts" / "delay_model.joblib"


def _row(order: Order) -> dict:
    # Only information known at order placement is permitted as an input.
    created = order.created_at
    promised = order.promised_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if promised.tzinfo is None:
        promised = promised.replace(tzinfo=timezone.utc)
    return {"quantity": order.quantity, "priority": order.priority,
            "lead_days": max(0.0, (promised - created).total_seconds() / 86400),
            "weekday": created.weekday(), "sku": order.sku}


def _features(orders: list[Order]) -> list[dict]:
    return [_row(o) for o in orders]


def _matrix(rows: list[dict]):
    # DataFrame column names preserve sklearn's reproducible feature contract.
    import pandas as pd
    return pd.DataFrame(rows, columns=FEATURES)


def _model() -> Pipeline:
    transform = ColumnTransformer([
        ("numeric", "passthrough", NUMERIC),
        ("sku", OneHotEncoder(handle_unknown="ignore"), ["sku"]),
    ])
    return Pipeline([
        ("transform", transform),
        ("classifier", RandomForestClassifier(n_estimators=100, min_samples_leaf=4,
                                              max_depth=5, random_state=42, n_jobs=1)),
    ])


def train_model(db: Session, model_path: Path = MODEL_PATH) -> dict:
    delivered = db.scalars(select(Order).where(Order.status == "delivered").order_by(Order.created_at, Order.id)).all()
    valid = [o for o in delivered if o.actual_delivered_at is not None]
    if len(valid) < 60:
        raise ValueError("At least 60 delivered orders with timestamps are required for model training")
    split = int(len(valid) * 0.8)
    training, holdout = valid[:split], valid[split:]
    y_train = np.array([int(o.actual_delivered_at > o.promised_at) for o in training])
    y_test = np.array([int(o.actual_delivered_at > o.promised_at) for o in holdout])
    if len(set(y_train)) < 2:
        raise ValueError("Training records must include both delayed and on-time orders")
    model = _model()
    model.fit(_matrix(_features(training)), y_train)
    positive_index = list(model.named_steps["classifier"].classes_).index(1)
    probabilities = model.predict_proba(_matrix(_features(holdout)))[:, positive_index]
    predicted = (probabilities >= 0.5).astype(int)
    base = np.full(len(y_test), int(y_train.mean() >= 0.5))
    auc = float(roc_auc_score(y_test, probabilities)) if len(set(y_test)) == 2 else None
    report = {
        "synthetic": True,
        "data_source": "synthetic warehouse demonstration",
        "model": "RandomForestClassifier",
        "evaluation": "chronological 80/20 holdout (no shuffled split)",
        "trained_on": len(training), "tested_on": len(holdout),
        "positive_class_rate_training": round(float(y_train.mean()), 4),
        "holdout_delay_rate": round(float(y_test.mean()), 4),
        "accuracy": round(float(accuracy_score(y_test, predicted)), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_test, predicted)), 4),
        "precision": round(float(precision_score(y_test, predicted, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, predicted, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, predicted, zero_division=0)), 4),
        "roc_auc": round(auc, 4) if auc is not None else None,
        "majority_baseline_accuracy": round(float(accuracy_score(y_test, base)), 4),
        "features": FEATURES,
        "limitations": "Synthetic training labels; small holdout; not validated on real enterprise data.",
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "report": report}, model_path)
    return report


def predict_pending(db: Session, model_path: Path = MODEL_PATH, *, sku: str | None = None, limit: int = 100) -> dict:
    if not model_path.exists():
        raise ValueError("No trained model found. Train a model first.")
    # Only load model artifacts generated locally by this application; pickle-backed joblib is unsafe for untrusted files.
    artifact = joblib.load(model_path)
    query = select(Order).where(Order.status == "pending").order_by(Order.id)
    if sku:
        query = query.where(Order.sku == sku)
    orders = db.scalars(query.limit(limit)).all()
    if not orders:
        return {"synthetic": True, "model": artifact["report"]["model"], "predictions": [], "high_risk_count": 0}
    pipeline = artifact["model"]
    positive_index = list(pipeline.named_steps["classifier"].classes_).index(1)
    probabilities = pipeline.predict_proba(_matrix(_features(orders)))[:, positive_index]
    predictions = []
    for order, risk in zip(orders, probabilities):
        score = round(float(risk), 4)
        predictions.append({"order_id": order.id, "sku": order.sku,
                            "quantity": order.quantity, "priority": order.priority,
                            "delay_probability": score,
                            "risk_level": "high" if score >= 0.65 else "medium" if score >= 0.35 else "low"})
    return {"synthetic": True, "model": artifact["report"]["model"],
            "high_risk_count": sum(p["risk_level"] == "high" for p in predictions),
            "predictions": predictions}


def current_report(model_path: Path = MODEL_PATH) -> dict | None:
    if not model_path.exists():
        return None
    return joblib.load(model_path)["report"]
