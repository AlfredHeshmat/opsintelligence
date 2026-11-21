"""New metadata-only governance guarantees; no external network connections."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.connectors import ConnectorRegistration
from app.models.identity import SecurityAudit
from test_enterprise_security import fixture_client, login, auth


def test_connector_governance_lifecycle_and_audit(fixture_client):
    client, engine, (org, other_org) = fixture_client
    owner = auth(login(client, 'alpha@example.com', 'correct-horse-unique-one').json()['access_token'])
    viewer = auth(login(client, 'viewer@example.com', 'correct-horse-unique-viewer').json()['access_token'])
    outsider = auth(login(client, 'beta@example.com', 'correct-horse-unique-two').json()['access_token'])
    base = f'/api/v1/enterprise/organisations/{org}/connectors'
    payload = {'display_name': 'Farm crop planning demo', 'kind': 'sql', 'provider': 'postgresql',
               'purpose': 'Planning with synthetic crop allocation data', 'data_classification': 'confidential'}
    assert client.post(base, json={**payload, 'access_token': 'secret'}, headers=owner).status_code == 422
    assert client.post(base, json={**payload, 'host': '127.0.0.1'}, headers=owner).status_code == 422
    assert client.post(base, json={**payload, 'purpose': 'short'}, headers=owner).status_code == 422
    created = client.post(base, json=payload, headers=owner)
    assert created.status_code == 201, created.text
    record = created.json()
    assert record['data_classification'] == 'confidential'
    assert record['execution_enabled'] is False
    url = f'{base}/{record["id"]}'
    assert client.post(f'{url}/request-review', headers=viewer).status_code == 403
    assert client.post(f'{url}/request-review', headers=outsider).status_code == 404
    assert client.post(f'{url}/approve-metadata', headers=owner).status_code == 409
    assert client.post(f'{url}/request-review', headers=owner).json()['status'] == 'pending_review'
    assert client.post(f'{url}/request-review', headers=owner).status_code == 409
    approved = client.post(f'{url}/approve-metadata', headers=owner)
    assert approved.status_code == 200
    assert approved.json()['status'] == 'metadata_approved'
    assert approved.json()['execution_enabled'] is False
    assert approved.json()['reviewed_at'] is not None
    assert client.post(f'{url}/approve-metadata', headers=owner).status_code == 409
    assert client.post(f'{url}/disable', headers=viewer).status_code == 403
    assert client.post(f'{url}/disable', headers=owner).json()['status'] == 'disabled'
    assert client.post(f'{url}/disable', headers=owner).status_code == 409
    assert client.get(f'/api/v1/enterprise/organisations/{other_org}/connectors', headers=owner).status_code == 404
    assert client.post(f'/api/v1/enterprise/organisations/{other_org}/connectors/{record["id"]}/disable', headers=owner).status_code == 404
    events = client.get(f'/api/v1/enterprise/organisations/{org}/audit', headers=owner).json()
    assert [e['action'] for e in events[:4]] == [
        'connector.disabled', 'connector.metadata_approved',
        'connector.review_requested', 'connector.registered',
    ]
    with Session(engine) as db:
        stored = db.scalar(select(ConnectorRegistration).where(ConnectorRegistration.id == record['id']))
        assert stored.status == 'disabled'
        assert stored.reviewed_by is not None
        assert len(db.scalars(select(SecurityAudit).where(SecurityAudit.organisation_id == org)).all()) >= 4
    assert client.post(f'{url}/test', headers=owner).status_code == 404
    assert client.delete(url, headers=owner).status_code == 204
    assert client.get(base, headers=owner).json() == []
