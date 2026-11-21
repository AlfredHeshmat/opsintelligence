"""Deny by default; no credentials accepted; cross-tenant connectors invisible."""
from sqlalchemy import select
from app.models.connectors import ConnectorRegistration
from test_enterprise_security import fixture_client, login, auth


def test_catalogue_requires_identity(fixture_client):
    client,_,_ = fixture_client
    assert client.get('/api/v1/enterprise/connector-types').status_code == 401
    token=login(client,'alpha@example.com','correct-horse-unique-one').json()['access_token']
    resp=client.get('/api/v1/enterprise/connector-types',headers=auth(token))
    assert resp.status_code == 200
    assert not resp.json()['live_integrations_enabled']
    assert all(not c['execution_supported'] and not c['credentials_supported'] for c in resp.json()['connectors'])


def test_registration_tenant_permissions_and_secret_rejection(fixture_client):
    client,engine,(a,b)=fixture_client
    owner=login(client,'alpha@example.com','correct-horse-unique-one').json()['access_token']
    outsider=login(client,'beta@example.com','correct-horse-unique-two').json()['access_token']
    viewer=login(client,'viewer@example.com','correct-horse-unique-viewer').json()['access_token']
    url=f'/api/v1/enterprise/organisations/{a}/connectors'
    good={'display_name':'Test warehouse DB','kind':'sql','provider':'postgresql'}
    assert client.post(url,json=good).status_code==401
    assert client.post(url,json=good,headers=auth(viewer)).status_code==403
    assert client.post(url,json=good,headers=auth(outsider)).status_code==404
    assert client.post(url,json={**good,'password':'do-not-store'},headers=auth(owner)).status_code==422
    assert client.post(url,json={**good,'kind':'mcp'},headers=auth(owner)).status_code==422
    created=client.post(url,json=good,headers=auth(owner))
    assert created.status_code==201,created.text
    record=created.json()
    assert record['status']=='not_configured'
    assert 'password' not in str(record)
    assert len(client.get(url,headers=auth(owner)).json())==1
    assert client.get(url,headers=auth(outsider)).status_code==404
    assert client.get(f'/api/v1/enterprise/organisations/{b}/connectors',headers=auth(owner)).status_code==404
    with engine.connect() as db:
        from sqlalchemy.orm import Session
        with Session(bind=db) as session:
            saved=session.scalars(select(ConnectorRegistration)).all()
            assert len(saved)==1
            assert saved[0].organisation_id==a
    assert client.delete(f'{url}/{record["id"]}',headers=auth(viewer)).status_code==403
    assert client.delete(f'/api/v1/enterprise/organisations/{b}/connectors/{record["id"]}',headers=auth(outsider)).status_code==404
    assert client.delete(f'{url}/{record["id"]}',headers=auth(owner)).status_code==204
    assert client.get(url,headers=auth(owner)).json()==[]


def test_no_endpoints_can_test_connections(fixture_client):
    client,_,(a,_)=fixture_client
    t=login(client,'alpha@example.com','correct-horse-unique-one').json()['access_token']
    assert client.post(f'/api/v1/enterprise/organisations/{a}/connectors/1/test',headers=auth(t)).status_code==404
