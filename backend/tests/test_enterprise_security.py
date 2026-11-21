"""Executable authorization gates; SQLite isolates tests from development PostgreSQL."""
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
from app.models.identity import Membership, Organisation, OrganisationProject, SecurityAudit, SessionToken, User
from app.security.passwords import hash_password, verify_password


@pytest.fixture
def fixture_client(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'postgresql+psycopg://test:test@localhost/test')
    get_settings.cache_clear()
    engine = create_engine('sqlite+pysqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        one = Organisation(name='Alpha')
        two = Organisation(name='Beta')
        a = User(email='alpha@example.com', password_hash=hash_password('correct-horse-unique-one'), failed_logins=0)
        b = User(email='beta@example.com', password_hash=hash_password('correct-horse-unique-two'), failed_logins=0)
        v = User(email='viewer@example.com', password_hash=hash_password('correct-horse-unique-viewer'), failed_logins=0)
        db.add_all([one,two,a,b,v]);db.flush()
        db.add_all([Membership(organisation_id=one.id,user_id=a.id,role='owner'), Membership(organisation_id=two.id,user_id=b.id,role='owner'), Membership(organisation_id=one.id,user_id=v.id,role='viewer')]);db.commit()
        ids = (one.id,two.id)
    monkeypatch.setattr('app.main.create_database_engine', lambda settings: MagicMock())
    app = create_app()
    def get_test_db():
        with Session(engine) as db:yield db
    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as client:
        yield client,engine,ids
    engine.dispose()
    get_settings.cache_clear()


def login(client,email,password):
    return client.post('/api/v1/enterprise/auth/login',json={'email':email,'password':password})


def auth(token):return {'Authorization': f'Bearer {token}'}


def test_password_hash_is_salted_and_validated():
    a=hash_password('long-enough-password')
    b=hash_password('long-enough-password')
    assert a != b
    assert verify_password('long-enough-password',a)
    assert not verify_password('wrong-password',a)


def test_login_me_and_revocation(fixture_client):
    client, engine, (a,b) = fixture_client
    assert client.get('/api/v1/enterprise/auth/me').status_code == 401
    assert login(client,'alpha@example.com','wrong-password').status_code == 401
    ok = login(client,'alpha@example.com','correct-horse-unique-one')
    assert ok.status_code == 200
    token = ok.json()['access_token']
    assert token not in str(client.get('/api/v1/enterprise/auth/me',headers=auth(token)).json())
    me=client.get('/api/v1/enterprise/auth/me', headers=auth(token))
    assert me.status_code == 200
    assert me.json()['organisations'][0]['id'] == a
    with Session(engine) as db:
        assert db.scalar(select(SessionToken)).token_digest != token
    assert client.post('/api/v1/enterprise/auth/logout',headers=auth(token)).status_code == 204
    assert client.get('/api/v1/enterprise/auth/me',headers=auth(token)).status_code == 401


def test_tenant_boundary_and_roles(fixture_client):
    client,engine,(a,b) = fixture_client
    token=login(client,'alpha@example.com','correct-horse-unique-one').json()['access_token']
    other=login(client,'beta@example.com','correct-horse-unique-two').json()['access_token']
    viewer=login(client,'viewer@example.com','correct-horse-unique-viewer').json()['access_token']
    root='/api/v1/enterprise/organisations/'
    assert client.post(f'{root}{a}/projects',json={'name':'Farm optimiser','industry_id':'agriculture'},headers=auth(token)).status_code == 201
    assert len(client.get(f'{root}{a}/projects',headers=auth(token)).json()) == 1
    assert client.get(f'{root}{a}/projects',headers=auth(other)).status_code == 404
    assert client.get(f'{root}{b}/projects',headers=auth(token)).status_code == 404
    assert client.post(f'{root}{a}/projects',json={'name':'Exploit','industry_id':'agriculture'},headers=auth(viewer)).status_code == 403
    assert client.get(f'{root}{a}/projects',headers=auth(viewer)).status_code == 200
    assert client.get(f'{root}{a}/members',headers=auth(viewer)).status_code == 403
    assert client.get(f'{root}{a}/audit',headers=auth(viewer)).status_code == 403
    assert client.get(f'{root}{a}/audit',headers=auth(token)).json()[0]['action']=='project.created'
    assert client.post(f'{root}{a}/projects',json={'name':'Invalid','industry_id':'does-not-exist'},headers=auth(token)).status_code == 422
    with Session(engine) as db:
        assert len(db.scalars(select(OrganisationProject)).all()) == 1
        assert len(db.scalars(select(SecurityAudit)).all()) >= 1


def test_membership_administration(fixture_client):
    client,engine,(a,b)=fixture_client
    token=login(client,'alpha@example.com','correct-horse-unique-one').json()['access_token']
    viewer=login(client,'viewer@example.com','correct-horse-unique-viewer').json()['access_token']
    url=f'/api/v1/enterprise/organisations/{a}/members'
    assert client.post(url,json={'email':'beta@example.com','role':'analyst'},headers=auth(viewer)).status_code==403
    assert client.post(url,json={'email':'beta@example.com','role':'analyst'},headers=auth(token)).status_code==201
    assert client.post(url,json={'email':'beta@example.com','role':'analyst'},headers=auth(token)).status_code==409
    with Session(engine) as db:
        assert db.scalar(select(Membership).where(Membership.organisation_id==a,Membership.role=='analyst')) is not None


def test_account_lockout_and_recovery(fixture_client):
    client,engine,_=fixture_client
    for _ in range(5):
        assert login(client,'alpha@example.com','incorrect').status_code==401
    assert login(client,'alpha@example.com','correct-horse-unique-one').status_code==429
    with Session(engine) as db:
        from datetime import timedelta, timezone, datetime
        u=db.scalar(select(User).where(User.email=='alpha@example.com'))
        u.locked_until=datetime.now(timezone.utc)-timedelta(seconds=1)
        db.commit()
    assert login(client,'alpha@example.com','correct-horse-unique-one').status_code==200


def test_expired_session_and_nonmember_exclusion(fixture_client):
    client,engine,(a,b)=fixture_client
    token=login(client,'beta@example.com','correct-horse-unique-two').json()['access_token']
    assert client.get(f'/api/v1/enterprise/organisations/{a}/audit',headers=auth(token)).status_code==404
    with Session(engine) as db:
        from datetime import timedelta, timezone, datetime
        session=db.scalar(select(SessionToken))
        session.expires_at=datetime.now(timezone.utc)-timedelta(minutes=1)
        db.commit()
    assert client.get('/api/v1/enterprise/auth/me',headers=auth(token)).status_code==401
