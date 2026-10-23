"""Tests for CORS configuration and origin restrictions."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app
from src.config import Settings


def test_cors_origins_list_parsing():
    s = Settings(
        CORS_ORIGINS="http://localhost:3000, https://admin.sinahotels.com , https://sinabernini.it"
    )
    assert s.cors_origins_list == [
        "http://localhost:3000",
        "https://admin.sinahotels.com",
        "https://sinabernini.it",
    ]


def test_cors_origins_list_default_when_empty():
    s = Settings(CORS_ORIGINS="")
    assert s.cors_origins_list == ["http://localhost:3000"]


def test_cors_allowed_origin():
    with TestClient(app) as client:
        # Preflight OPTIONS request
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
        # Ensure allow_credentials is not set to true
        assert response.headers.get("access-control-allow-credentials") is None


def test_cors_disallowed_origin():
    with TestClient(app) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") is None
