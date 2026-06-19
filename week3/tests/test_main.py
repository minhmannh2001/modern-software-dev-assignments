from unittest.mock import MagicMock, patch

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
def clear_stores():
    auth_module._token_store.clear()
    auth_module._pending_authorizations.clear()
    auth_module._auth_code_store.clear()
    auth_module._client_store.clear()
    yield
    auth_module._token_store.clear()
    auth_module._pending_authorizations.clear()
    auth_module._auth_code_store.clear()
    auth_module._client_store.clear()


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


def test_register_returns_client_id(client):
    res = client.post("/register", json={"redirect_uris": ["http://localhost:54321/callback"]})
    assert res.status_code == 200
    assert "client_id" in res.json()


def test_register_without_redirect_uris_returns_400(client):
    res = client.post("/register", json={"client_name": "Claude CLI"})
    assert res.status_code == 400


def test_register_bypasses_middleware(client):
    res = client.post("/register", json={"redirect_uris": ["http://localhost:54321/callback"]})
    assert res.status_code == 200


# --- PKCE auth code flow ---

def _register_client(client, redirect_uri="http://localhost:54321/callback") -> str:
    res = client.post("/register", json={"redirect_uris": [redirect_uri]})
    return res.json()["client_id"]


_PKCE_PARAMS = {
    "redirect_uri": "http://localhost:54321/callback",
    "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
    "code_challenge_method": "S256",
    "state": "my-mcp-state",
}


def test_authorize_with_valid_client_redirects_to_github(client):
    client_id = _register_client(client)
    res = client.get("/oauth/authorize", params={"client_id": client_id, **_PKCE_PARAMS})
    assert res.is_redirect
    assert "github.com/login/oauth/authorize" in res.headers["location"]


def test_authorize_unknown_client_id_returns_400(client):
    res = client.get("/oauth/authorize", params={
        "client_id": "unknown-client",
        **_PKCE_PARAMS,
    })
    assert res.status_code == 400


def test_authorize_mismatched_redirect_uri_returns_400(client):
    client_id = _register_client(client)
    res = client.get("/oauth/authorize", params={
        "client_id": client_id,
        "redirect_uri": "http://evil.com/callback",
        "code_challenge": "abc",
        "code_challenge_method": "S256",
        "state": "s",
    })
    assert res.status_code == 400


def test_callback_redirects_to_client_with_auth_code(client):
    token_resp = MagicMock()
    token_resp.status_code = 200
    token_resp.json.return_value = {"access_token": "gh_secret"}
    token_resp.raise_for_status.return_value = None
    user_resp = MagicMock()
    user_resp.status_code = 200
    user_resp.json.return_value = {"login": "octocat"}
    user_resp.raise_for_status.return_value = None

    auth_module._pending_authorizations["github-state-123"] = {
        "code_challenge": "abc",
        "redirect_uri": "http://localhost:54321/callback",
        "client_id": "test-client",
        "mcp_state": "my-mcp-state",
    }

    with patch("server.auth.httpx.post", return_value=token_resp), \
         patch("server.auth.httpx.get", return_value=user_resp):
        res = client.get("/oauth/callback", params={"code": "ghcode", "state": "github-state-123"})

    assert res.is_redirect
    location = res.headers["location"]
    assert "http://localhost:54321/callback" in location
    assert "code=" in location
    assert "state=my-mcp-state" in location


def test_unauthenticated_mcp_request_returns_401(client):
    res = client.post("/mcp")
    assert res.status_code == 401


def test_oauth_authorize_reachable_without_token(client):
    client_id = _register_client(client)
    res = client.get("/oauth/authorize", params={"client_id": client_id, **_PKCE_PARAMS})
    assert res.is_redirect
    assert "github.com" in res.headers["location"]
