import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

import server.auth as auth_module
from server.auth import BearerTokenMiddleware


async def protected_route(request: Request):
    user = getattr(request.state, "user", None)
    return JSONResponse({"user": user})


async def authorize_stub(request: Request):
    return JSONResponse({"ok": True})


async def callback_stub(request: Request):
    return JSONResponse({"ok": True})


def make_app():
    app = Starlette(routes=[
        Route("/oauth/authorize", authorize_stub),
        Route("/oauth/callback", callback_stub),
        Route("/protected", protected_route),
    ])
    app.add_middleware(BearerTokenMiddleware)
    return app


@pytest.fixture(autouse=True)
def clear_token_store():
    auth_module._token_store.clear()
    yield
    auth_module._token_store.clear()


@pytest.fixture
def client():
    return TestClient(make_app(), raise_server_exceptions=True)


def test_oauth_authorize_bypasses_middleware(client):
    res = client.get("/oauth/authorize")
    assert res.status_code == 200


def test_oauth_callback_bypasses_middleware(client):
    res = client.get("/oauth/callback")
    assert res.status_code == 200


def test_valid_bearer_token_reaches_handler_with_user(client):
    auth_module._token_store["valid-uuid"] = {"github_username": "octocat"}
    res = client.get("/protected", headers={"Authorization": "Bearer valid-uuid"})
    assert res.status_code == 200
    assert res.json()["user"]["github_username"] == "octocat"


def test_unknown_bearer_token_returns_401(client):
    res = client.get("/protected", headers={"Authorization": "Bearer unknown-token"})
    assert res.status_code == 401
    assert res.json() == {"error": "unauthorized"}


def test_no_authorization_header_returns_401(client):
    res = client.get("/protected")
    assert res.status_code == 401
    assert res.json() == {"error": "unauthorized"}


def test_malformed_authorization_header_returns_401(client):
    res = client.get("/protected", headers={"Authorization": "Bearer"})
    assert res.status_code == 401
    assert res.json() == {"error": "unauthorized"}
