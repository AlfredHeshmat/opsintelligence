
"""Regression tests for the public-only OpsIntelligence deployment."""

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def get_api_paths(app):
    """Collect API endpoints from the generated OpenAPI schema."""
    return set(app.openapi()["paths"].keys())


def test_public_demo_excludes_enterprise_routes(monkeypatch):
    """Public mode should expose demo endpoints but not enterprise APIs."""
    from app import main

    settings = Settings(
        database_url="postgresql+psycopg://demo:demo@localhost:5432/demo",
        cors_origins=["https://example.pages.dev"],
        ops_public_demo_only=True,
    )

    monkeypatch.setattr(main, "get_settings", lambda: settings)

    app = create_app()
    paths = get_api_paths(app)

    assert "/api/v1/operations/overview" in paths
    assert "/api/v1/industry-pilots/catalogue" in paths

    assert not any(
        path.startswith("/api/v1/enterprise")
        for path in paths
    )

    assert not any(
        path.startswith("/api/v1/connectors")
        for path in paths
    )


def test_local_mode_keeps_enterprise_routes(monkeypatch):
    """Local mode should retain enterprise functionality."""
    from app import main

    settings = Settings(
        database_url="postgresql+psycopg://demo:demo@localhost:5432/demo",
        ops_public_demo_only=False,
    )

    monkeypatch.setattr(main, "get_settings", lambda: settings)

    app = create_app()
    paths = get_api_paths(app)

    assert "/api/v1/operations/overview" in paths

    assert any(
        path.startswith("/api/v1/enterprise")
        for path in paths
    )


def test_public_mode_refuses_enterprise_access_and_demo_reset(monkeypatch):
    """Public mode must reject protected enterprise and reset requests."""
    from app import main

    settings = Settings(
        database_url="postgresql+psycopg://demo:demo@localhost:5432/demo",
        cors_origins=["https://example.pages.dev"],
        ops_public_demo_only=True,
    )

    monkeypatch.setattr(main, "get_settings", lambda: settings)

    app = create_app()
    client = TestClient(app)

    # Public demo datasets cannot be reset by visitors.
    response = client.post(
        "/api/v1/data/seed",
        json={"seed": 99},
    )
    assert response.status_code == 403

    # Enterprise authentication must not be publicly accessible.
    response = client.post(
        "/api/v1/enterprise/auth/login",
        json={},
    )
    assert response.status_code == 404

    # Enterprise project APIs must also be inaccessible.
    response = client.get(
        "/api/v1/enterprise/organisations",
    )
    assert response.status_code == 404
