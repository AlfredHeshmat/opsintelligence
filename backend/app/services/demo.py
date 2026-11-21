"""Deterministic demo data; never confuse it with live enterprise data."""
import random
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal
from sqlalchemy import delete, select, func
from sqlalchemy.orm import Session
from app.models import Capacity, Inventory, Order, ShippingOption, OptimizationRun

SKUS = ('SKU-A','SKU-B','SKU-C','SKU-D','SKU-E')

def seed_demo(db: Session, count: int = 240, seed: int = 42) -> dict:
    if not 20 <= count <= 3000:
        raise ValueError('count must be 20..3000')
    # Never destroy a user's existing data; demo is seeded only into an empty database.
    if db.scalar(select(func.count()).select_from(Order)):
        raise ValueError('Orders already exist; refusing to overwrite operational data')
    rng = random.Random(seed)
    base = datetime.now(timezone.utc).replace(hour=8,minute=0,second=0,microsecond=0) - timedelta(days=29)
    inventory = [Inventory(sku=sku,available_quantity=300, reserved_quantity=0) for sku in SKUS]
    db.add_all(inventory)
    db.add_all([ShippingOption(name='economy',transit_days=4,cost_per_order=Decimal('7.00')),
                ShippingOption(name='express',transit_days=1,cost_per_order=Decimal('17.00'))])
    db.add_all([Capacity(date=(base+timedelta(days=i)).date(),labour_hours=28,handling_units=90) for i in range(31)])
    orders=[]
    for i in range(count):
        day=i%30
        created=base + timedelta(days=day,hours=rng.randint(0,9))
        qty=rng.randint(1,9)
        priority=rng.choices([1,2,3],[.55,.3,.15])[0]
        promised=created + timedelta(days=rng.randint(2,5))
        finished=i < int(count*.72)
        delayed=rng.random()<(.3 if day%7 in (4,5) else .12)
        delivered=promised+timedelta(hours=rng.randint(1,36)) if delayed else promised-timedelta(hours=rng.randint(1,12))
        orders.append(Order(sku=rng.choice(SKUS),quantity=qty,priority=priority,created_at=created,promised_at=promised,
                            revenue=Decimal(30+qty*18),status='delivered' if finished else 'pending',
                            actual_delivered_at=delivered if finished else None))
    db.add_all(orders)
    db.commit()
    return {'inserted_orders':count,'seed':seed,'synthetic':True}
