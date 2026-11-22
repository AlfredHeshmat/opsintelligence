"""Secure-by-default integration contract tests; no external database required."""
import json

from app.services.readonly_postgres import provisioned_profile
from test_enterprise_security import fixture_client, login, auth


def _registered(client, org, headers, classification='internal'):
    base = f'/api/v1/enterprise/organisations/{org}/connectors'
    created = client.post(base, headers=headers, json={
        'display_name': 'Synthetic readonly test', 'kind': 'sql',
        'provider': 'postgresql', 'data_classification': classification,
        'purpose': 'Synthetic data integration security tests',
    })
    assert created.status_code == 201, created.text
    identifier = created.json()['id']
    return f'{base}/{identifier}', identifier


def test_disabled_by_default_and_approval_required(fixture_client, monkeypatch):
    client, _, (org, other) = fixture_client
    owner = auth(login(client, 'alpha@example.com', 'correct-horse-unique-one').json()['access_token'])
    outsider = auth(login(client, 'beta@example.com', 'correct-horse-unique-two').json()['access_token'])
    viewer = auth(login(client, 'viewer@example.com', 'correct-horse-unique-viewer').json()['access_token'])
    url, identifier = _registered(client, org, owner)
    check = url + '/connection-check'
    preview = url + '/table-preview'
    assert client.post(check).status_code == 401
    assert client.post(check, headers=viewer).status_code == 403
    assert client.post(check, headers=outsider).status_code == 404
    assert client.post(f'/api/v1/enterprise/organisations/{other}/connectors/{identifier}/connection-check', headers=owner).status_code == 404
    assert client.post(check, headers=owner).status_code == 409
    assert client.post(url + '/request-review', headers=owner).status_code == 200
    assert client.post(url + '/approve-metadata', headers=owner).status_code == 200
    assert client.post(check, headers=owner).status_code == 503
    assert client.post(preview, headers=owner, json={'table':'public.demo'}).status_code == 503
    assert client.post(preview, headers=owner, json={'table':'public.demo', 'sql':'DROP TABLE demo'}).status_code == 422
    assert client.post(url + '/disable', headers=owner).status_code == 200
    assert client.post(check, headers=owner).status_code == 409


def test_exact_tenant_mapping_and_identifier_rejection(monkeypatch):
    monkeypatch.setenv('OPS_READONLY_CONNECTORS_ENABLED', 'true')
    config = {'1': {'5': {'dsn': 'postgresql://readonly:secret@db/synthetic', 'tables': ['public.demo']}}}
    monkeypatch.setenv('OPS_PG_CONNECTOR_BINDINGS_JSON', json.dumps(config))
    profile = provisioned_profile(1, 5)
    assert profile is not None
    assert profile.tables == ('public.demo',)
    assert provisioned_profile(2, 5) is None
    assert provisioned_profile(1, 6) is None
    config['1']['5']['tables'] = ['public.demo; DROP TABLE users']
    monkeypatch.setenv('OPS_PG_CONNECTOR_BINDINGS_JSON', json.dumps(config))
    assert provisioned_profile(1, 5) is None
    monkeypatch.setenv('OPS_READONLY_CONNECTORS_ENABLED', 'false')
    assert provisioned_profile(1, 5) is None


def test_preview_allowlist_and_audit(fixture_client, monkeypatch):
    client, _, (org, _) = fixture_client
    owner = auth(login(client, 'alpha@example.com', 'correct-horse-unique-one').json()['access_token'])
    url, identifier = _registered(client, org, owner)
    assert client.post(url + '/request-review', headers=owner).status_code == 200
    assert client.post(url + '/approve-metadata', headers=owner).status_code == 200
    config = {str(org): {str(identifier): {'dsn': 'postgresql://reader@db/synthetic', 'tables': ['public.demo']}}}
    monkeypatch.setenv('OPS_READONLY_CONNECTORS_ENABLED', 'true')
    monkeypatch.setenv('OPS_PG_CONNECTOR_BINDINGS_JSON', json.dumps(config))
    monkeypatch.setattr('app.api.connectors.check_connection', lambda profile: {'status':'reachable','read_only':True,'allowed_tables':list(profile.tables)})
    monkeypatch.setattr('app.api.connectors.preview_table', lambda profile, table: {'table':table,'columns':['id'],'rows':[{'id':'1'}],'row_limit':25,'sample_only':True})
    assert client.post(url + '/connection-check', headers=owner).json()['read_only'] is True
    assert client.post(url + '/table-preview', headers=owner, json={'table':'public.other'}).status_code == 422
    good = client.post(url + '/table-preview', headers=owner, json={'table':'public.demo'})
    assert good.status_code == 200 and good.json()['rows'] == [{'id':'1'}]
    events = client.get(f'/api/v1/enterprise/organisations/{org}/audit', headers=owner).json()
    assert events[0]['action'] == 'connector.table_previewed'
    assert events[1]['action'] == 'connector.connection_checked'


def test_confidential_classification_cannot_preview(fixture_client, monkeypatch):
    client, _, (org, _) = fixture_client
    owner = auth(login(client, 'alpha@example.com', 'correct-horse-unique-one').json()['access_token'])
    url, identifier = _registered(client, org, owner, 'confidential')
    assert client.post(url + '/request-review', headers=owner).status_code == 200
    assert client.post(url + '/approve-metadata', headers=owner).status_code == 200
    monkeypatch.setenv('OPS_READONLY_CONNECTORS_ENABLED', 'true')
    monkeypatch.setenv('OPS_PG_CONNECTOR_BINDINGS_JSON', json.dumps({str(org): {str(identifier): {'dsn':'postgresql://reader@db/demo','tables':['public.demo']}}}))
    assert client.post(url + '/connection-check', headers=owner).status_code == 403
