from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.core.config import get_settings
from app.main import create_app


def test_registry_routes_and_contract_validation(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'postgresql+psycopg://test:test@localhost/test')
    get_settings.cache_clear()
    monkeypatch.setattr('app.main.create_database_engine', lambda settings: MagicMock())
    with TestClient(create_app()) as client:
        response = client.get('/api/v1/workspace/registry')
        assert response.status_code == 200
        assert len(response.json()['industries']) >= 20
        definition = client.get('/api/v1/workspace/registry/agriculture')
        assert definition.status_code == 200
        assert definition.json()['industry']['support_level'] == 'data_contract_defined'
        decision = client.post('/api/v1/workspace/decision/validate', json={
            'industry': 'technology', 'subindustry': 'cloud_infrastructure',
            'objective': 'minimize_cost', 'constraints': [
                {'metric_id': 'latency_sla', 'operator': '<=', 'value': 200, 'unit': 'ms'}]})
        assert decision.status_code == 200
        assert decision.json()['specification_valid'] is True
        assert decision.json()['solver_executable_for_this_spec'] is False
        invalid = client.post('/api/v1/workspace/decision/validate', json={
            'industry': 'agriculture', 'subindustry': 'saas', 'objective': 'maximize_margin'})
        assert invalid.status_code == 422

    get_settings.cache_clear()
