import base64
import hashlib
import uuid
from urllib.parse import urlencode

import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Route

_OAUTH_PATHS = {"/oauth/authorize", "/oauth/callback"}
_PUBLIC_PATHS = _OAUTH_PATHS | {
    "/.well-known/oauth-protected-resource",
    "/.well-known/oauth-authorization-server",
    "/register",
    "/oauth/token",
}

_client_store: dict[str, dict] = {}


class BearerTokenMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, server_url: str = "http://localhost:8000"):
        super().__init__(app)
        self._www_authenticate = (
            f'Bearer realm="MCP Weather Server", '
            f'resource_metadata="{server_url}/.well-known/oauth-protected-resource"'
        )

    async def dispatch(self, request: Request, call_next):
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split(" ", 1)
        token = parts[1].strip() if len(parts) == 2 and parts[0] == "Bearer" else ""

        user_info = lookup(token) if token else None
        if user_info is None:
            return JSONResponse(
                {"error": "unauthorized"},
                status_code=401,
                headers={"WWW-Authenticate": self._www_authenticate},
            )

        request.state.user = user_info
        return await call_next(request)

_GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USER_URL = "https://api.github.com/user"

_pending_authorizations: dict[str, dict] = {}  # github_state → {code_challenge, redirect_uri, client_id, mcp_state}
_auth_code_store: dict[str, dict] = {}          # auth_code → {github_username, code_challenge, redirect_uri, client_id, expires_at}
_token_store: dict[str, dict] = {}


def lookup(token: str) -> dict | None:
    return _token_store.get(token)


def _verify_pkce(code_verifier: str, code_challenge: str) -> bool:
    digest = hashlib.sha256(code_verifier.encode()).digest()
    computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return computed == code_challenge


def make_token_router() -> list[Route]:
    async def token(request: Request):
        form = await request.form()
        code = form.get("code", "")
        code_verifier = form.get("code_verifier", "")
        client_id = form.get("client_id", "")
        redirect_uri = form.get("redirect_uri", "")

        stored = _auth_code_store.get(code)
        if stored is None:
            return JSONResponse({"error": "invalid_grant"}, status_code=400)
        if stored["client_id"] != client_id:
            return JSONResponse({"error": "client_id mismatch"}, status_code=400)
        if stored["redirect_uri"] != redirect_uri:
            return JSONResponse({"error": "redirect_uri mismatch"}, status_code=400)
        if not _verify_pkce(code_verifier, stored["code_challenge"]):
            return JSONResponse({"error": "invalid code_verifier"}, status_code=400)

        del _auth_code_store[code]

        opaque_token = str(uuid.uuid4())
        _token_store[opaque_token] = {"github_username": stored["github_username"]}
        return JSONResponse({"access_token": opaque_token, "token_type": "Bearer"})

    return [Route("/oauth/token", token, methods=["POST"])]


def make_registration_router() -> list[Route]:
    async def register(request: Request):
        body = await request.json()
        redirect_uris = body.get("redirect_uris")
        if not redirect_uris:
            return JSONResponse({"error": "redirect_uris is required"}, status_code=400)
        client_id = str(uuid.uuid4())
        _client_store[client_id] = {
            "redirect_uris": redirect_uris,
            "client_name": body.get("client_name", ""),
        }
        return JSONResponse({"client_id": client_id, "redirect_uris": redirect_uris})

    return [Route("/register", register, methods=["POST"])]


def make_metadata_router(config) -> list[Route]:
    async def protected_resource(request: Request):
        return JSONResponse({
            "resource": config.server_url,
            "authorization_servers": [config.server_url],
        })

    async def authorization_server(request: Request):
        base = config.server_url
        return JSONResponse({
            "issuer": base,
            "authorization_endpoint": f"{base}/oauth/authorize",
            "token_endpoint": f"{base}/oauth/token",
            "registration_endpoint": f"{base}/register",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code"],
            "code_challenge_methods_supported": ["S256"],
        })

    return [
        Route("/.well-known/oauth-protected-resource", protected_resource),
        Route("/.well-known/oauth-authorization-server", authorization_server),
    ]


def make_auth_router(config) -> list[Route]:
    async def authorize(request: Request):
        client_id = request.query_params.get("client_id", "")
        redirect_uri = request.query_params.get("redirect_uri", "")
        code_challenge = request.query_params.get("code_challenge", "")
        mcp_state = request.query_params.get("state", "")

        if client_id not in _client_store:
            return JSONResponse({"error": "unknown client_id"}, status_code=400)
        if redirect_uri not in _client_store[client_id]["redirect_uris"]:
            return JSONResponse({"error": "redirect_uri not registered for client"}, status_code=400)

        github_state = str(uuid.uuid4())
        _pending_authorizations[github_state] = {
            "code_challenge": code_challenge,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "mcp_state": mcp_state,
        }
        params = {
            "client_id": config.github_client_id,
            "redirect_uri": config.redirect_uri,
            "scope": "read:user",
            "state": github_state,
        }
        return RedirectResponse(f"{_GITHUB_AUTHORIZE_URL}?{urlencode(params)}")

    async def callback(request: Request):
        github_state = request.query_params.get("state", "")
        if github_state not in _pending_authorizations:
            return JSONResponse({"error": "invalid state"}, status_code=400)
        pending = _pending_authorizations.pop(github_state)

        code = request.query_params.get("code", "")
        try:
            token_resp = httpx.post(
                _GITHUB_TOKEN_URL,
                data={
                    "client_id": config.github_client_id,
                    "client_secret": config.github_client_secret,
                    "code": code,
                    "redirect_uri": config.redirect_uri,
                },
                headers={"Accept": "application/json"},
                timeout=10,
            )
            token_resp.raise_for_status()
            github_token = token_resp.json().get("access_token")
            if not github_token:
                return JSONResponse({"error": "token exchange failed"}, status_code=502)

            user_resp = httpx.get(
                _GITHUB_USER_URL,
                headers={"Authorization": f"Bearer {github_token}", "Accept": "application/json"},
                timeout=10,
            )
            user_resp.raise_for_status()
            github_username = user_resp.json().get("login", "unknown")
        except httpx.HTTPError as e:
            return JSONResponse({"error": f"GitHub API error: {e}"}, status_code=502)

        auth_code = str(uuid.uuid4())
        _auth_code_store[auth_code] = {
            "github_username": github_username,
            "code_challenge": pending["code_challenge"],
            "redirect_uri": pending["redirect_uri"],
            "client_id": pending["client_id"],
        }
        redirect_url = (
            f"{pending['redirect_uri']}?code={auth_code}&state={pending['mcp_state']}"
        )
        return RedirectResponse(redirect_url)

    return [
        Route("/oauth/authorize", authorize),
        Route("/oauth/callback", callback),
    ]
