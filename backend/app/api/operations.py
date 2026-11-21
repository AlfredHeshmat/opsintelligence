from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, selectinload
from app.api.health import get_engine
from app.models import Capacity, Order, OptimizationRun
from app.services.analytics import overview, anomalies
from app.services.demo import seed_demo
from app.services.optimizer import solve_allocation, serialize_run

router=APIRouter(prefix='/api/v1',tags=['operations'])

def get_db(engine: Annotated[Engine,Depends(get_engine)]):
    with Session(engine) as session:
        yield session

DB=Annotated[Session,Depends(get_db)]

class SeedRequest(BaseModel):
    count:int=Field(default=240,ge=20,le=3000)
    seed:int=42

class SolveRequest(BaseModel):
    handling_capacity:int | None=Field(default=None,ge=0,le=100000)
    labour_hours:int | None=Field(default=None,ge=0,le=100000)

@router.post('/data/seed')
def seed(request:SeedRequest,db:DB):
    try: return seed_demo(db,count=request.count,seed=request.seed)
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc

@router.get('/operations/overview')
def operations_overview(db:DB):
    return overview(db)

@router.get('/orders')
def orders(db:DB,limit:int=Query(default=50,ge=1,le=200),offset:int=Query(default=0,ge=0)):
    values=db.scalars(select(Order).order_by(Order.id).offset(offset).limit(limit)).all()
    return [{'id':o.id,'sku':o.sku,'quantity':o.quantity,'priority':o.priority,
             'status':o.status,'promised_at':o.promised_at.isoformat(),'revenue':float(o.revenue)} for o in values]

@router.get('/capacity')
def capacity(db:DB):
    return [{'date':c.date.isoformat(),'handling_units':c.handling_units,'labour_hours':c.labour_hours} for c in db.scalars(select(Capacity).order_by(Capacity.date.desc()).limit(30)).all()]

@router.get('/anomalies')
def list_anomalies(db:DB):
    return {'synthetic':True,'alerts':anomalies(db)}

@router.post('/optimization/solve')
def solve(request:SolveRequest,db:DB):
    try: return serialize_run(solve_allocation(db,handling_capacity=request.handling_capacity,labour_hours=request.labour_hours))
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc

@router.get('/optimization/runs/{run_id}')
def optimization_run(run_id:int,db:DB):
    run=db.scalar(select(OptimizationRun).options(selectinload(OptimizationRun.decisions)).where(OptimizationRun.id==run_id))
    if run is None: raise HTTPException(status_code=404,detail='Run not found')
    return serialize_run(run)
