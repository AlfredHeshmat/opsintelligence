from collections import defaultdict
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Capacity, Inventory, Order

def overview(db: Session):
    orders=db.scalars(select(Order)).all()
    delivered=[o for o in orders if o.status=='delivered' and o.actual_delivered_at is not None]
    late=[o for o in delivered if o.actual_delivered_at>o.promised_at]
    pending=[o for o in orders if o.status=='pending']
    by_day=defaultdict(lambda: {'orders':0,'delayed':0})
    for o in orders:
        k=o.created_at.date().isoformat()
        by_day[k]['orders']+=1
        if o.status=='delivered' and o.actual_delivered_at and o.actual_delivered_at>o.promised_at:
            by_day[k]['delayed']+=1
    capacity=db.scalars(select(Capacity).order_by(Capacity.date.desc()).limit(1)).first()
    return {'synthetic':True,'total_orders':len(orders),'pending_orders':len(pending),
            'delivered_orders':len(delivered),'late_deliveries':len(late),
            'on_time_rate':round(100*(len(delivered)-len(late))/len(delivered),2) if delivered else None,
            'pending_units':sum(o.quantity for o in pending),'daily_handling_capacity':capacity.handling_units if capacity else None,
            'inventory_units':sum(max(0,i.available_quantity-i.reserved_quantity) for i in db.scalars(select(Inventory)).all()),
            'trend':[{'date':k,**v} for k,v in sorted(by_day.items())]}

def anomalies(db:Session):
    data=overview(db)
    result=[]
    if data['pending_units'] and data['daily_handling_capacity'] and data['pending_units']>data['daily_handling_capacity']:
        result.append({'severity':'high','metric':'pending_units','value':data['pending_units'],'message':'Pending units exceed one day of handling capacity'})
    if data['on_time_rate'] is not None and data['on_time_rate']<85:
        result.append({'severity':'medium','metric':'on_time_rate','value':data['on_time_rate'],'message':'Delivery performance below 85% threshold'})
    return result
