"""SKU-level product metrics with an explicit time horizon and auditable definitions."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Order, Inventory


def product_performance(db: Session, *, days: int = 30, sku: str | None = None):
    if days not in (7, 30, 90, 365):
        raise ValueError("days must be 7, 30, 90 or 365")
    # Historical demo records are dated relative to when seeded; use the newest record date
    # as the reporting anchor so the snapshot remains reproducible when reviewed later.
    latest = db.scalar(select(Order.created_at).order_by(Order.created_at.desc()).limit(1))
    if not latest:
        return {"synthetic": True, "period_days": days, "products": [], "totals": {"orders": 0, "units": 0, "revenue": 0, "on_time_rate": None}}
    cutoff = latest - timedelta(days=days)
    query = select(Order).where(Order.created_at >= cutoff, Order.created_at <= latest)
    if sku:
        query = query.where(Order.sku == sku)
    orders = db.scalars(query).all()
    inventory = {row.sku: max(0, row.available_quantity - row.reserved_quantity) for row in db.scalars(select(Inventory)).all()}
    groups = defaultdict(list)
    for item in orders:
        groups[item.sku].append(item)
    products = []
    for code, entries in sorted(groups.items()):
        delivered = [o for o in entries if o.status == "delivered" and o.actual_delivered_at]
        late = sum(o.actual_delivered_at > o.promised_at for o in delivered)
        products.append({"sku": code, "orders": len(entries), "units": sum(o.quantity for o in entries),
                         "revenue": round(sum(float(o.revenue) for o in entries), 2),
                         "pending_units": sum(o.quantity for o in entries if o.status == "pending"),
                         "available_inventory": inventory.get(code, 0),
                         "on_time_rate": round(100 * (len(delivered) - late) / len(delivered), 2) if delivered else None})
    delivered_all = [o for o in orders if o.status == "delivered" and o.actual_delivered_at]
    late_all = sum(o.actual_delivered_at > o.promised_at for o in delivered_all)
    return {"synthetic": True, "period_days": days,
            "as_of_date": latest.date().isoformat(),
            "products": products,
            "totals": {"orders": len(orders), "units": sum(o.quantity for o in orders),
                       "revenue": round(sum(float(o.revenue) for o in orders), 2),
                       "on_time_rate": round(100*(len(delivered_all)-late_all)/len(delivered_all), 2) if delivered_all else None}}
