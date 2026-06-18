from unittest.mock import MagicMock

import pytest
from starlette.testclient import TestClient

import server.auth as auth_module
from server.main import create_app

_FAKE_CONFIG = MagicMock()
_FAKE_CONFIG.github_client_id = "test_id"
_FAKE_CONFIG.github_client_secret = "test_secret"
_FAKE_CONFIG.redirect_uri = "http://localhost:8000/oauth/callback"


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


def test_unauthenticated_mcp_request_returns_401(client):
    res = client.post("/mcp")
    assert res.status_code == 401


def test_oauth_authorize_reachable_without_token(client):
    res = client.get("/oauth/authorize")
    assert res.is_redirect
    assert "github.com" in res.headers["location"]
