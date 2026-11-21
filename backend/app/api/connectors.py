"""Tenant-isolated metadata-only connector catalogue, no secret ingestion or outbound requests."""
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.api.enterprise import Principal, DB, access, audit
from app.models.connectors import ConnectorRegistration
from app.services.connector_catalogue import ConnectorRequest, catalogue, validate_pair

router = APIRouter(prefix='/api/v1/enterprise', tags=['enterprise-connectors'])

@router.get('/connector-types')
def connector_types(auth: Principal):
    return {'connectors':catalogue(), 'live_integrations_enabled':False}

def public_model(reg: ConnectorRegistration):
    return {'id':reg.id,'organisation_id':reg.organisation_id,'display_name':reg.display_name,
            'kind':reg.kind,'provider':reg.provider,'status':reg.status,'created_at':reg.created_at.isoformat()}

@router.get('/organisations/{org_id}/connectors')
def list_connectors(org_id: int, auth: Principal, db: DB):
    user,_=auth
    access(db,user,org_id)
    regs=db.scalars(select(ConnectorRegistration).where(ConnectorRegistration.organisation_id==org_id).order_by(ConnectorRegistration.id)).all()
    return [public_model(reg) for reg in regs]

@router.post('/organisations/{org_id}/connectors', status_code=201)
def register_connector(org_id: int, payload:ConnectorRequest,auth:Principal, db:DB):
    user,_=auth
    access(db,user,org_id,'admin')
    if not validate_pair(payload.kind,payload.provider):
        raise HTTPException(422,detail='Provider and connector category do not match')
    reg=ConnectorRegistration(organisation_id=org_id,display_name=payload.display_name.strip(),kind=payload.kind,
                              provider=payload.provider,status='not_configured')
    db.add(reg);db.flush()
    audit(db,user.id,org_id,'connector.registered','connector',reg.id)
    db.commit();db.refresh(reg)
    return public_model(reg)

@router.delete('/organisations/{org_id}/connectors/{connector_id}', status_code=204)
def delete_connector(org_id:int,connector_id:int,auth:Principal,db:DB):
    user,_=auth
    access(db,user,org_id,'admin')
    reg=db.scalar(select(ConnectorRegistration).where(ConnectorRegistration.id==connector_id,ConnectorRegistration.organisation_id==org_id))
    if reg is None:raise HTTPException(404,detail='Connector not found')
    db.delete(reg)
    audit(db,user.id,org_id,'connector.deleted','connector',connector_id)
    db.commit()
