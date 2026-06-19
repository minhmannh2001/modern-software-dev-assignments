from unittest.mock import MagicMock

import pytest
from starlette.testclient import TestClient

import server.auth as auth_module
from server.main import create_app

_FAKE_CONFIG = MagicMock()
_FAKE_CONFIG.github_client_id = "test_id"
_FAKE_CONFIG.github_client_secret = "test_secret"
_FAKE_CONFIG.redirect_uri = "http://localhost:8000/oauth/callback"
_FAKE_CONFIG.server_url = "http://localhost:8000"


@pytest.fixture(autouse=True)
def clear_token_store():
    auth_module._token_store.clear()
    auth_module._pending_states.clear()
    yield
    auth_module._token_store.clear()
    auth_module._pending_states.clear()


@pytest.fixture
def client():
    app = create_app(_FAKE_CONFIG)
    return TestClient(app, raise_server_exceptions=False, follow_redirects=False)


def test_protected_resource_metadata_returns_correct_shape(client):
    res = client.get("/.well-known/oauth-protected-resource")
    assert res.status_code == 200
    body = res.json()
    assert body["resource"] == "http://localhost:8000"
    assert "http://localhost:8000" in body["authorization_servers"]


def test_authorization_server_metadata_returns_required_fields(client):
    res = client.get("/.well-known/oauth-authorization-server")
    assert res.status_code == 200
    body = res.json()
    assert body["issuer"] == "http://localhost:8000"
    assert body["authorization_endpoint"] == "http://localhost:8000/oauth/authorize"
    assert body["token_endpoint"] == "http://localhost:8000/oauth/token"
    assert body["registration_endpoint"] == "http://localhost:8000/register"
    assert "S256" in body["code_challenge_methods_supported"]


def test_well_known_endpoints_bypass_middleware(client):
    assert client.get("/.well-known/oauth-protected-resource").status_code == 200
    assert client.get("/.well-known/oauth-authorization-server").status_code == 200


def test_unauthenticated_request_returns_www_authenticate_header(client):
    res = client.post("/mcp")
    assert res.status_code == 401
    assert "WWW-Authenticate" in res.headers
    assert "resource_metadata" in res.headers["WWW-Authenticate"]
    assert "/.well-known/oauth-protected-resource" in res.headers["WWW-Authenticate"]


def test_metadata_server_url_reflects_config(client):
    res = client.get("/.well-known/oauth-protected-resource")
    assert "http://localhost:8000" in res.json()["resource"]


def test_unauthenticated_mcp_request_returns_401(client):
    res = client.post("/mcp")
    assert res.status_code == 401


def test_oauth_authorize_reachable_without_token(client):
    res = client.get("/oauth/authorize")
    assert res.is_redirect
    assert "github.com" in res.headers["location"]
