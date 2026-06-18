from unittest.mock import MagicMock, patch

import pytest
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.routing import Route

import server.auth as auth_module
from server.auth import lookup, make_auth_router

_FAKE_CONFIG = MagicMock()
_FAKE_CONFIG.github_client_id = "test_client_id"
_FAKE_CONFIG.github_client_secret = "test_secret"
_FAKE_CONFIG.redirect_uri = "http://localhost:8000/oauth/callback"


@pytest.fixture(autouse=True)
def clear_stores():
    auth_module._pending_states.clear()
    auth_module._token_store.clear()
    yield
    auth_module._pending_states.clear()
    auth_module._token_store.clear()


@pytest.fixture
def client():
    router = make_auth_router(_FAKE_CONFIG)
    app = Starlette(routes=router)
    return TestClient(app, follow_redirects=False)


def _mock_github(username: str = "octocat"):
    token_resp = MagicMock()
    token_resp.status_code = 200
    token_resp.json.return_value = {"access_token": "gh_secret_token"}
    token_resp.raise_for_status.return_value = None

    user_resp = MagicMock()
    user_resp.status_code = 200
    user_resp.json.return_value = {"login": username}
    user_resp.raise_for_status.return_value = None

    return token_resp, user_resp


def test_authorize_redirects_to_github(client):
    res = client.get("/oauth/authorize")
    assert res.is_redirect
    assert "github.com/login/oauth/authorize" in res.headers["location"]


def test_authorize_stores_state(client):
    client.get("/oauth/authorize")
    assert len(auth_module._pending_states) == 1


def test_callback_unknown_state_returns_400(client):
    res = client.get("/oauth/callback?code=abc&state=not-a-real-state")
    assert res.status_code == 400


def test_callback_success_returns_token_and_user(client):
    token_resp, user_resp = _mock_github("octocat")
    with patch("server.auth.httpx.post", return_value=token_resp), \
         patch("server.auth.httpx.get", return_value=user_resp):
        auth_module._pending_states.add("valid-state")
        res = client.get("/oauth/callback?code=abc&state=valid-state")
    assert res.status_code == 200
    body = res.json()
    assert "token" in body
    assert body["user"] == "octocat"


def test_callback_github_token_not_stored(client):
    token_resp, user_resp = _mock_github()
    with patch("server.auth.httpx.post", return_value=token_resp), \
         patch("server.auth.httpx.get", return_value=user_resp):
        auth_module._pending_states.add("valid-state")
        client.get("/oauth/callback?code=abc&state=valid-state")
    assert lookup("gh_secret_token") is None


def test_lookup_valid_token_returns_user_info(client):
    token_resp, user_resp = _mock_github("octocat")
    with patch("server.auth.httpx.post", return_value=token_resp), \
         patch("server.auth.httpx.get", return_value=user_resp):
        auth_module._pending_states.add("valid-state")
        res = client.get("/oauth/callback?code=abc&state=valid-state")
    opaque_token = res.json()["token"]
    info = lookup(opaque_token)
    assert info is not None
    assert info["github_username"] == "octocat"


def test_lookup_unknown_token_returns_none():
    assert lookup("non-existent-token") is None
