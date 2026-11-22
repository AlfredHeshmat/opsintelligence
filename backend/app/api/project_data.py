"""Private project CSV pilot: authenticated, organisation-scoped, bounded and auditable.

This API intentionally does not use demo orders or expose an optimisation endpoint.
"""
from hashlib import sha256
from typing import Annotated
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.enterprise import access, audit, principal
from app.api.operations import get_db
from app.models.identity import OrganisationProject, User
from app.models.project_data import ProjectDataset, ProjectOrder
from app.services.project_csv import MAX_BYTES, ImportValidationError, parse_project_orders

router = APIRouter(prefix='/api/v1/enterprise/organisations/{org_id}/projects/{project_id}', tags=['enterprise-project-data'])
DB = Annotated[Session, Depends(get_db)]
AUTH = Annotated[tuple, Depends(principal)]


def project_for(db: Session, user: User, org_id: int, project_id: int, role: str = 'viewer'):
    access(db, user, org_id, role)
    project = db.scalar(select(OrganisationProject).where(
        OrganisationProject.id == project_id, OrganisationProject.organisation_id == org_id))
    if project is None:
        raise HTTPException(404, 'Project not found')
    return project


def dataset_info(dataset: ProjectDataset | None):
    if not dataset:
        return None
    return {'id': dataset.id, 'row_count': dataset.row_count,
            'source_filename': dataset.source_filename, 'sha256': dataset.sha256,
            'imported_at': dataset.imported_at.isoformat()}


@router.post('/orders/import', status_code=201)
def import_orders(org_id: int, project_id: int, auth: AUTH, db: DB,
                  raw: Annotated[bytes, Body(media_type='text/csv')],
                  x_filename: Annotated[str | None, Header()] = None):
    user, _ = auth
    project = project_for(db, user, org_id, project_id, 'analyst')
    if project.industry_id != 'logistics':
        raise HTTPException(422, 'CSV order import is currently supported only for logistics projects')
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, 'CSV exceeds the 2 MB import limit')
    try:
        orders = parse_project_orders(raw, org_id, project_id)
    except ImportValidationError as exc:
        raise HTTPException(422, str(exc)) from None
    filename = (x_filename or 'orders.csv').strip()
    if not filename.lower().endswith('.csv') or len(filename) > 180 or '/' in filename or '\\' in filename or any(ord(c) < 32 for c in filename):
        raise HTTPException(422, 'Invalid CSV filename')
    prior = db.scalar(select(ProjectDataset).where(
        ProjectDataset.project_id == project_id, ProjectDataset.organisation_id == org_id))
    digest = sha256(raw).hexdigest()
    if prior is not None and prior.sha256 == digest:
        raise HTTPException(409, 'This exact dataset is already imported into the project')
    # Atomic replacement: all records validate before we delete any existing data.
    db.execute(delete(ProjectOrder).where(ProjectOrder.project_id == project_id, ProjectOrder.organisation_id == org_id))
    if prior:
        db.delete(prior)
        db.flush()
    dataset = ProjectDataset(organisation_id=org_id, project_id=project_id,
                             source_filename=filename, sha256=digest,
                             row_count=len(orders), imported_by=user.id)
    db.add(dataset)
    db.add_all(orders)
    db.flush()
    audit(db, user.id, org_id, 'project.dataset_imported', 'project', project_id)
    db.commit()
    db.refresh(dataset)
    return {'dataset': dataset_info(dataset), 'message': 'Validated CSV imported into this project'}


@router.get('/orders/summary')
def orders_summary(org_id: int, project_id: int, auth: AUTH, db: DB):
    user, _ = auth
    project_for(db, user, org_id, project_id)
    dataset = db.scalar(select(ProjectDataset).where(
        ProjectDataset.project_id == project_id, ProjectDataset.organisation_id == org_id))
    if dataset is None:
        return {'dataset': None, 'total_orders': 0, 'pending_orders': 0,
                'late_deliveries': 0, 'gross_sales_aud': 0, 'estimated_margin_aud': 0,
                'warehouse_count': 0, 'status_counts': {}}
    orders = db.scalars(select(ProjectOrder).where(
        ProjectOrder.organisation_id == org_id, ProjectOrder.project_id == project_id)).all()
    from decimal import Decimal
    gross = sum((o.unit_price_aud * o.quantity for o in orders), Decimal('0'))
    margin = sum(((o.unit_price_aud-o.unit_cost_aud)*o.quantity-o.shipping_cost_aud for o in orders), Decimal('0'))
    statuses: dict[str, int] = {}
    for order in orders:
        statuses[order.status] = statuses.get(order.status, 0) + 1
    return {'dataset': dataset_info(dataset), 'total_orders': len(orders),
            'pending_orders': statuses.get('pending', 0),
            'late_deliveries': sum(1 for o in orders if o.shipped_date is not None and o.shipped_date > o.promised_date),
            'gross_sales_aud': float(gross), 'estimated_margin_aud': float(margin),
            'warehouse_count': len({o.warehouse_id for o in orders}),
            'status_counts': statuses}


@router.get('/orders')
def list_project_orders(org_id: int, project_id: int, auth: AUTH, db: DB,
                        limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0),
                        sku: str | None = Query(None, max_length=64),
                        status: str | None = Query(None, max_length=20)):
    user, _ = auth
    project_for(db, user, org_id, project_id)
    filters = [ProjectOrder.organisation_id == org_id, ProjectOrder.project_id == project_id]
    if sku:
        filters.append(ProjectOrder.sku == sku.strip())
    if status:
        if status not in ('pending','shipped','delivered','cancelled'):
            raise HTTPException(422, 'Invalid status filter')
        filters.append(ProjectOrder.status == status)
    total = db.scalar(select(func.count()).select_from(ProjectOrder).where(*filters)) or 0
    values = db.scalars(select(ProjectOrder).where(*filters).order_by(ProjectOrder.id).offset(offset).limit(limit)).all()
    return {'total': total, 'limit': limit, 'offset': offset,
            'items': [{'order_id': o.order_id, 'order_date': o.order_date.isoformat(), 'warehouse_id': o.warehouse_id,
                       'sku': o.sku, 'quantity': o.quantity, 'priority': o.priority, 'status': o.status,
                       'promised_date': o.promised_date.isoformat(),
                       'shipped_date': o.shipped_date.isoformat() if o.shipped_date else None,
                       'unit_price_aud': float(o.unit_price_aud), 'unit_cost_aud': float(o.unit_cost_aud),
                       'shipping_cost_aud': float(o.shipping_cost_aud), 'destination_region': o.destination_region}
                      for o in values]}

# Phase 4E final: project-specific decision planning. Always authoritative on the backend.
from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.project_optimisation import ProjectOptimisationRun
from app.services.project_optimisation import MODEL_VERSION, plan_dispatch


class DispatchPlanRequest(BaseModel):
    handling_capacity: int = Field(ge=0, le=1_000_000)
    defer_penalty_aud_per_unit: Decimal = Field(default=Decimal('12.00'), ge=Decimal('0.01'), le=Decimal('1000'), decimal_places=2)


def run_view(run: ProjectOptimisationRun, current_hash: str | None):
    return {'id': run.id, 'project_id': run.project_id, 'model_version': run.model_version,
            'status': run.status, 'solver_message': run.solver_message,
            'created_at': run.created_at.isoformat(), 'dataset_sha256': run.dataset_sha256,
            'dataset_current': run.dataset_sha256 == current_hash,
            'handling_capacity': run.handling_capacity,
            'defer_penalty_aud_per_unit': float(run.defer_penalty_aud_per_unit),
            'pending_orders': run.pending_orders,
            'baseline_cost_aud': float(run.baseline_cost_aud) if run.baseline_cost_aud is not None else None,
            'objective_cost_aud': float(run.objective_cost_aud) if run.objective_cost_aud is not None else None,
            'decisions': run.decisions}


@router.post('/optimisation/solve', status_code=201)
def solve_project(org_id: int, project_id: int, payload: DispatchPlanRequest, auth: AUTH, db: DB):
    user, _ = auth
    project = project_for(db, user, org_id, project_id, 'analyst')
    if project.industry_id != 'logistics':
        raise HTTPException(422, 'This project model supports logistics orders only')
    dataset = db.scalar(select(ProjectDataset).where(
        ProjectDataset.organisation_id == org_id, ProjectDataset.project_id == project_id))
    if dataset is None:
        raise HTTPException(422, 'Import and validate a project orders CSV before running optimisation')
    orders = db.scalars(select(ProjectOrder).where(
        ProjectOrder.organisation_id == org_id, ProjectOrder.project_id == project_id,
        ProjectOrder.status == 'pending').order_by(ProjectOrder.order_id)).all()
    try:
        result = plan_dispatch(orders, payload.handling_capacity, payload.defer_penalty_aud_per_unit)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    record = ProjectOptimisationRun(
        organisation_id=org_id, project_id=project_id, created_by=user.id,
        dataset_sha256=dataset.sha256, model_version=MODEL_VERSION,
        status=result['status'], solver_message=result['solver_message'],
        handling_capacity=payload.handling_capacity,
        defer_penalty_aud_per_unit=payload.defer_penalty_aud_per_unit,
        pending_orders=result['pending_orders'],
        baseline_cost_aud=result['baseline_cost_aud'],
        objective_cost_aud=result['objective_cost_aud'], decisions=result['decisions'])
    db.add(record)
    db.flush()
    audit(db, user.id, org_id, 'project.optimisation_run', 'project_optimisation', record.id)
    db.commit()
    db.refresh(record)
    return run_view(record, dataset.sha256)


@router.get('/optimisation/runs')
def project_runs(org_id: int, project_id: int, auth: AUTH, db: DB,
                 limit: int = Query(10, ge=1, le=30), offset: int = Query(0, ge=0)):
    user, _ = auth
    project_for(db, user, org_id, project_id, 'viewer')
    dataset = db.scalar(select(ProjectDataset).where(
        ProjectDataset.organisation_id == org_id, ProjectDataset.project_id == project_id))
    filters = [ProjectOptimisationRun.organisation_id == org_id, ProjectOptimisationRun.project_id == project_id]
    count = db.scalar(select(func.count()).select_from(ProjectOptimisationRun).where(*filters)) or 0
    rows = db.scalars(select(ProjectOptimisationRun).where(*filters).order_by(
        ProjectOptimisationRun.id.desc()).limit(limit).offset(offset)).all()
    return {'total': count, 'limit': limit, 'offset': offset,
            'items': [run_view(row, dataset.sha256 if dataset else None) for row in rows]}


@router.get('/optimisation/runs/{run_id}')
def project_run_detail(org_id: int, project_id: int, run_id: int, auth: AUTH, db: DB):
    user, _ = auth
    project_for(db, user, org_id, project_id, 'viewer')
    run = db.scalar(select(ProjectOptimisationRun).where(
        ProjectOptimisationRun.id == run_id, ProjectOptimisationRun.organisation_id == org_id,
        ProjectOptimisationRun.project_id == project_id))
    if run is None:
        raise HTTPException(404, 'Optimisation run not found')
    dataset = db.scalar(select(ProjectDataset).where(
        ProjectDataset.organisation_id == org_id, ProjectDataset.project_id == project_id))
    return run_view(run, dataset.sha256 if dataset else None)
