import uuid
from urllib.parse import urlencode

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Route

_GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USER_URL = "https://api.github.com/user"

_pending_states: set[str] = set()
_token_store: dict[str, dict] = {}


def lookup(token: str) -> dict | None:
    return _token_store.get(token)


def make_auth_router(config) -> list[Route]:
    async def authorize(request: Request):
        state = str(uuid.uuid4())
        _pending_states.add(state)
        params = {
            "client_id": config.github_client_id,
            "redirect_uri": config.redirect_uri,
            "scope": "read:user",
            "state": state,
        }
        return RedirectResponse(f"{_GITHUB_AUTHORIZE_URL}?{urlencode(params)}")

    async def callback(request: Request):
        state = request.query_params.get("state", "")
        if state not in _pending_states:
            return JSONResponse({"error": "invalid state"}, status_code=400)
        _pending_states.discard(state)

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

        opaque_token = str(uuid.uuid4())
        _token_store[opaque_token] = {"github_username": github_username}
        return JSONResponse({"token": opaque_token, "user": github_username})

    return [
        Route("/oauth/authorize", authorize),
        Route("/oauth/callback", callback),
    ]
