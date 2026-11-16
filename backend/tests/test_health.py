from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.api.health import get_engine
from app.core.config import get_settings
from app.main import create_app


@pytest.fixture
def client(monkeypatch):
    # Tests use a fake engine, so they don't need PostgreSQL.
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost/test",
    )
    get_settings.cache_clear()

    app = create_app()
    engine = MagicMock()
    app.dependency_overrides[get_engine] = lambda: engine

    try:
        with TestClient(app) as test_client:
            yield test_client, engine
    finally:
        get_settings.cache_clear()


def test_health_does_not_need_database(client):
    test_client, engine = client

    response = test_client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    engine.connect.assert_not_called()


def test_ready_when_database_connected(client):
    test_client, engine = client

    response = test_client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "connected",
    }
    engine.connect.assert_called_once()


def test_ready_when_database_unavailable(client):
    test_client, engine = client
    engine.connect.side_effect = OperationalError(
        "SELECT 1", {}, Exception("Connection failed")
    )

    response = test_client.get("/api/v1/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "database": "unavailable",
    }
    assert test_client.get("/api/v1/health").status_code == 200
