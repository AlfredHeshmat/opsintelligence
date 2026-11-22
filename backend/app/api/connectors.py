"""Tenant-isolated connector governance: no credentials and no outbound execution."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.api.enterprise import DB, Principal, access, audit
from app.models.connectors import ConnectorRegistration
from app.services.connector_catalogue import ConnectorRequest, catalogue, validate_pair
from app.services.readonly_postgres import (
    ConnectorExecutionError, ConnectorUnavailable, check_connection,
    preview_table, provisioned_profile,
)

router = APIRouter(prefix='/api/v1/enterprise', tags=['enterprise-connectors'])


@router.get('/connector-types')
def connector_types(auth: Principal):
    return {'connectors': catalogue(), 'live_integrations_enabled': False}


def public_model(reg: ConnectorRegistration) -> dict:
    return {
        'id': reg.id, 'organisation_id': reg.organisation_id,
        'display_name': reg.display_name, 'kind': reg.kind,
        'provider': reg.provider, 'status': reg.status,
        'purpose': reg.purpose, 'data_classification': reg.data_classification,
        'reviewed_at': reg.reviewed_at.isoformat() if reg.reviewed_at else None,
        'created_at': reg.created_at.isoformat(),
        'execution_enabled': False,
    }


@router.get('/organisations/{org_id}/connectors')
def list_connectors(org_id: int, auth: Principal, db: DB):
    user, _ = auth
    access(db, user, org_id)
    regs = db.scalars(
        select(ConnectorRegistration).where(
            ConnectorRegistration.organisation_id == org_id
        ).order_by(ConnectorRegistration.id)
    ).all()
    return [public_model(reg) for reg in regs]


@router.post('/organisations/{org_id}/connectors', status_code=201)
def register_connector(org_id: int, payload: ConnectorRequest, auth: Principal, db: DB):
    user, _ = auth
    access(db, user, org_id, 'admin')
    if not validate_pair(payload.kind, payload.provider):
        raise HTTPException(422, detail='Provider and connector category do not match')
    reg = ConnectorRegistration(
        organisation_id=org_id, display_name=payload.display_name.strip(),
        kind=payload.kind, provider=payload.provider, status='not_configured',
        purpose=payload.purpose.strip(), data_classification=payload.data_classification,
    )
    db.add(reg)
    db.flush()
    audit(db, user.id, org_id, 'connector.registered', 'connector', reg.id)
    db.commit()
    db.refresh(reg)
    return public_model(reg)


def get_connector(db: DB, org_id: int, connector_id: int) -> ConnectorRegistration:
    reg = db.scalar(select(ConnectorRegistration).where(
        ConnectorRegistration.id == connector_id,
        ConnectorRegistration.organisation_id == org_id,
    ))
    if reg is None:
        raise HTTPException(404, detail='Connector not found')
    return reg


@router.post('/organisations/{org_id}/connectors/{connector_id}/request-review')
def request_connector_review(org_id: int, connector_id: int, auth: Principal, db: DB):
    user, _ = auth
    access(db, user, org_id, 'admin')
    reg = get_connector(db, org_id, connector_id)
    if reg.status != 'not_configured':
        raise HTTPException(409, detail='Connector must be unconfigured to request review')
    reg.status = 'pending_review'
    audit(db, user.id, org_id, 'connector.review_requested', 'connector', reg.id)
    db.commit()
    db.refresh(reg)
    return public_model(reg)


@router.post('/organisations/{org_id}/connectors/{connector_id}/approve-metadata')
def approve_connector_metadata(org_id: int, connector_id: int, auth: Principal, db: DB):
    user, _ = auth
    access(db, user, org_id, 'owner')
    reg = get_connector(db, org_id, connector_id)
    if reg.status != 'pending_review':
        raise HTTPException(409, detail='Connector must be pending review')
    reg.status = 'metadata_approved'
    reg.reviewed_by = user.id
    reg.reviewed_at = datetime.now(timezone.utc)
    audit(db, user.id, org_id, 'connector.metadata_approved', 'connector', reg.id)
    db.commit()
    db.refresh(reg)
    return public_model(reg)


@router.post('/organisations/{org_id}/connectors/{connector_id}/disable')
def disable_connector(org_id: int, connector_id: int, auth: Principal, db: DB):
    user, _ = auth
    access(db, user, org_id, 'admin')
    reg = get_connector(db, org_id, connector_id)
    if reg.status == 'disabled':
        raise HTTPException(409, detail='Connector is already disabled')
    reg.status = 'disabled'
    audit(db, user.id, org_id, 'connector.disabled', 'connector', reg.id)
    db.commit()
    db.refresh(reg)
    return public_model(reg)


@router.delete('/organisations/{org_id}/connectors/{connector_id}', status_code=204)
def delete_connector(org_id: int, connector_id: int, auth: Principal, db: DB):
    user, _ = auth
    access(db, user, org_id, 'admin')
    reg = get_connector(db, org_id, connector_id)
    db.delete(reg)
    audit(db, user.id, org_id, 'connector.deleted', 'connector', connector_id)
    db.commit()


class PreviewRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    table: str = Field(min_length=3, max_length=127)


def execution_profile(db: DB, user, org_id: int, connector_id: int):
    access(db, user, org_id, 'admin')
    reg = get_connector(db, org_id, connector_id)
    if reg.provider != 'postgresql' or reg.status != 'metadata_approved':
        raise HTTPException(409, detail='Connector requires approved PostgreSQL metadata')
    if reg.data_classification not in ('public', 'internal'):
        raise HTTPException(403, detail='Only synthetic public/internal sources are permitted')
    profile = provisioned_profile(org_id, connector_id)
    if profile is None:
        raise HTTPException(503, detail='Read-only connector not provisioned by operator')
    return reg, profile


@router.post('/organisations/{org_id}/connectors/{connector_id}/connection-check')
def connection_check(org_id: int, connector_id: int, auth: Principal, db: DB):
    user, _ = auth
    reg, profile = execution_profile(db, user, org_id, connector_id)
    try:
        result = check_connection(profile)
    except ConnectorExecutionError:
        audit(db, user.id, org_id, 'connector.connection_check_failed', 'connector', reg.id)
        db.commit()
        raise HTTPException(502, detail='Read-only connection check failed')
    audit(db, user.id, org_id, 'connector.connection_checked', 'connector', reg.id)
    db.commit()
    return result


@router.post('/organisations/{org_id}/connectors/{connector_id}/table-preview')
def table_preview(org_id: int, connector_id: int, payload: PreviewRequest, auth: Principal, db: DB):
    user, _ = auth
    reg, profile = execution_profile(db, user, org_id, connector_id)
    if payload.table not in profile.tables:
        raise HTTPException(422, detail='Table not in operator allowlist')
    try:
        result = preview_table(profile, payload.table)
    except ConnectorUnavailable:
        raise HTTPException(422, detail='Table is not eligible for preview')
    except ConnectorExecutionError:
        audit(db, user.id, org_id, 'connector.preview_failed', 'connector', reg.id)
        db.commit()
        raise HTTPException(502, detail='Read-only preview failed')
    audit(db, user.id, org_id, 'connector.table_previewed', 'connector', reg.id)
    db.commit()
    return result
