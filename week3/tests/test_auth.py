from unittest.mock import MagicMock, patch

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

import server.auth as auth_module
from server.auth import lookup, make_auth_router

_FAKE_CONFIG = MagicMock()
_FAKE_CONFIG.github_client_id = "test_client_id"
_FAKE_CONFIG.github_client_secret = "test_secret"
_FAKE_CONFIG.redirect_uri = "http://localhost:8000/oauth/callback"

_TEST_CLIENT_ID = "test-client-id"
_TEST_REDIRECT_URI = "http://localhost:54321/callback"


@pytest.fixture(autouse=True)
def clear_stores():
    auth_module._pending_authorizations.clear()
    auth_module._auth_code_store.clear()
    auth_module._token_store.clear()
    auth_module._client_store.clear()
    # pre-register a test client so authorize calls work
    auth_module._client_store[_TEST_CLIENT_ID] = {"redirect_uris": [_TEST_REDIRECT_URI]}
    yield
    auth_module._pending_authorizations.clear()
    auth_module._auth_code_store.clear()
    auth_module._token_store.clear()
    auth_module._client_store.clear()


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


def _pending_state(mcp_state: str = "mcp-state") -> str:
    """Inject a pending authorization and return the github_state key."""
    github_state = "test-github-state"
    auth_module._pending_authorizations[github_state] = {
        "code_challenge": "test-challenge",
        "redirect_uri": _TEST_REDIRECT_URI,
        "client_id": _TEST_CLIENT_ID,
        "mcp_state": mcp_state,
    }
    return github_state


def test_authorize_redirects_to_github(client):
    res = client.get("/oauth/authorize", params={
        "client_id": _TEST_CLIENT_ID,
        "redirect_uri": _TEST_REDIRECT_URI,
        "code_challenge": "challenge",
        "code_challenge_method": "S256",
        "state": "mcp-state",
    })
    assert res.is_redirect
    assert "github.com/login/oauth/authorize" in res.headers["location"]


def test_authorize_stores_pending_authorization(client):
    client.get("/oauth/authorize", params={
        "client_id": _TEST_CLIENT_ID,
        "redirect_uri": _TEST_REDIRECT_URI,
        "code_challenge": "challenge",
        "code_challenge_method": "S256",
        "state": "mcp-state",
    })
    assert len(auth_module._pending_authorizations) == 1


def test_callback_unknown_state_returns_400(client):
    res = client.get("/oauth/callback?code=abc&state=not-a-real-state")
    assert res.status_code == 400


def test_callback_success_redirects_to_client_with_auth_code(client):
    token_resp, user_resp = _mock_github("octocat")
    github_state = _pending_state("my-mcp-state")
    with patch("server.auth.httpx.post", return_value=token_resp), \
         patch("server.auth.httpx.get", return_value=user_resp):
        res = client.get(f"/oauth/callback?code=abc&state={github_state}")
    assert res.is_redirect
    location = res.headers["location"]
    assert _TEST_REDIRECT_URI in location
    assert "code=" in location
    assert "state=my-mcp-state" in location


def test_callback_github_token_not_stored(client):
    token_resp, user_resp = _mock_github()
    github_state = _pending_state()
    with patch("server.auth.httpx.post", return_value=token_resp), \
         patch("server.auth.httpx.get", return_value=user_resp):
        client.get(f"/oauth/callback?code=abc&state={github_state}")
    assert lookup("gh_secret_token") is None


def test_callback_stores_auth_code_with_pkce_challenge(client):
    token_resp, user_resp = _mock_github("octocat")
    github_state = _pending_state()
    with patch("server.auth.httpx.post", return_value=token_resp), \
         patch("server.auth.httpx.get", return_value=user_resp):
        res = client.get(f"/oauth/callback?code=abc&state={github_state}")
    from urllib.parse import urlparse, parse_qs
    params = parse_qs(urlparse(res.headers["location"]).query)
    auth_code = params["code"][0]
    stored = auth_module._auth_code_store.get(auth_code)
    assert stored is not None
    assert stored["github_username"] == "octocat"
    assert stored["code_challenge"] == "test-challenge"


def test_lookup_unknown_token_returns_none():
    assert lookup("non-existent-token") is None
