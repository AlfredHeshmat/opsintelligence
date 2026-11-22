"""Private CSV importer: per-request RBAC, cross-tenant isolation, atomic replacement."""
from pathlib import Path
from io import StringIO
import csv
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.operations import get_db
from app.core.config import get_settings
from app.db.base import Base
from app.main import create_app
from app.models.identity import Membership, Organisation, OrganisationProject, User
from app.models.project_data import ProjectOrder, ProjectDataset
from app.security.passwords import hash_password
from app.services.project_csv import FIELDS, ImportValidationError, parse_project_orders


def raw_csv(rows):
    file=StringIO()
    writer=csv.DictWriter(file, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return file.getvalue().encode()


def sample_row(id='ORDER-1'):
    return dict(zip(FIELDS,[id,'2026-09-15','WH-01','SKU-001','2','standard',
                             '2026-09-20','2026-09-19','delivered','100.00','60.00','10.00','NSW']))


def test_parser_and_rejections():
    parsed=parse_project_orders(raw_csv([sample_row()]),1,10)
    assert len(parsed)==1 and parsed[0].quantity==2
    with pytest.raises(ImportValidationError,match='duplicate'):
        parse_project_orders(raw_csv([sample_row(),sample_row()]),1,10)
    with pytest.raises(ImportValidationError,match='CSV row 2'):
        parse_project_orders(raw_csv([dict(sample_row(),quantity='-7')]),1,10)
    with pytest.raises(ImportValidationError,match='columns'):
        parse_project_orders(b'x,y\na,b\n',1,10)
    with pytest.raises(ImportValidationError,match='2 MB'):
        parse_project_orders(b'x'*2_000_001,1,10)
    with pytest.raises(ImportValidationError,match='shipped_date'):
        parse_project_orders(raw_csv([dict(sample_row(),shipped_date='')]),1,10)


@pytest.fixture
def secure_project(monkeypatch):
    monkeypatch.setenv('DATABASE_URL','postgresql+psycopg://test:test@localhost/test')
    get_settings.cache_clear()
    engine=create_engine('sqlite+pysqlite:///:memory:',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        org1=Organisation(name='Acme');org2=Organisation(name='Other')
        owner=User(email='owner@test.example',password_hash=hash_password('valid-password-1'))
        outsider=User(email='other@test.example',password_hash=hash_password('valid-password-2'))
        viewer=User(email='viewer@test.example',password_hash=hash_password('valid-password-3'))
        db.add_all([org1,org2,owner,outsider,viewer]);db.flush()
        db.add_all([Membership(organisation_id=org1.id,user_id=owner.id,role='owner'),
                    Membership(organisation_id=org2.id,user_id=outsider.id,role='owner'),
                    Membership(organisation_id=org1.id,user_id=viewer.id,role='viewer')])
        project1=OrganisationProject(organisation_id=org1.id,name='Warehouse',industry_id='logistics')
        project2=OrganisationProject(organisation_id=org2.id,name='Other warehouse',industry_id='logistics')
        db.add_all([project1,project2]);db.commit()
        ids=(org1.id,project1.id,org2.id,project2.id)
    monkeypatch.setattr('app.main.create_database_engine',lambda settings:MagicMock())
    app=create_app()
    def get_test_db():
        with Session(engine) as db:yield db
    app.dependency_overrides[get_db]=get_test_db
    with TestClient(app) as client:
        def token(email,password):
            response=client.post('/api/v1/enterprise/auth/login',json={'email':email,'password':password})
            assert response.status_code==200
            return {'Authorization':'Bearer '+response.json()['access_token']}
        yield client,engine,ids,token('owner@test.example','valid-password-1'),token('other@test.example','valid-password-2'),token('viewer@test.example','valid-password-3')
    engine.dispose()
    get_settings.cache_clear()


def test_import_read_permissions_and_tenant_isolation(secure_project):
    client,engine,(org,project,other_org,other_project),owner,other,viewer=secure_project
    root=f'/api/v1/enterprise/organisations/{org}/projects/{project}'
    imported=client.post(root+'/orders/import',headers={**owner,'Content-Type':'text/csv','X-Filename':'acme.csv'},content=raw_csv([sample_row()]))
    assert imported.status_code==201,imported.text
    assert imported.json()['dataset']['row_count']==1
    assert client.get(root+'/orders/summary',headers=owner).json()['gross_sales_aud']==200
    assert client.get(root+'/orders/summary',headers=owner).json()['estimated_margin_aud']==70
    assert client.get(root+'/orders',headers=viewer).json()['items'][0]['order_id']=='ORDER-1'
    assert client.post(root+'/orders/import',headers={**viewer,'Content-Type':'text/csv'},content=raw_csv([sample_row('ORDER-2')])).status_code==403
    assert client.get(root+'/orders',headers=other).status_code==404
    assert client.get(root+'/orders/summary',headers=other).status_code==404
    assert client.post(root+'/orders/import',headers={**other,'Content-Type':'text/csv'},content=raw_csv([sample_row('ORDER-2')])).status_code==404
    guessed=f'/api/v1/enterprise/organisations/{other_org}/projects/{project}'
    assert client.get(guessed+'/orders',headers=other).status_code==404
    assert client.get(root+'/orders').status_code==401
    assert client.get(root+'/orders?status=invalid',headers=owner).status_code==422
    with Session(engine) as db:
        assert len(db.scalars(select(ProjectOrder)).all())==1


def test_atomic_invalid_import_and_replacement(secure_project):
    client,engine,(org,project,_,_),owner,other,viewer=secure_project
    root=f'/api/v1/enterprise/organisations/{org}/projects/{project}'
    def send(rows):return client.post(root+'/orders/import',headers={**owner,'Content-Type':'text/csv','X-Filename':'orders.csv'},content=raw_csv(rows))
    assert send([sample_row()]).status_code==201
    assert send([sample_row()]).status_code==409
    invalid=send([sample_row('NEW'),dict(sample_row('BROKEN'),quantity='0')])
    assert invalid.status_code==422
    assert client.get(root+'/orders',headers=owner).json()['items'][0]['order_id']=='ORDER-1'
    assert send([sample_row('NEW'),sample_row('NEW2')]).status_code==201
    data=client.get(root+'/orders?limit=1&offset=1',headers=owner).json()
    assert data['total']==2 and data['items'][0]['order_id']=='NEW2'
    with Session(engine) as db:
        assert len(db.scalars(select(ProjectDataset)).all())==1
        assert len(db.scalars(select(ProjectOrder)).all())==2
