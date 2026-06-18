# Issue 3: GitHub OAuth Flow

## What to build

Implement the GitHub Authorization Code OAuth flow inside `auth.py`. The server exposes two public HTTP routes that handle the full dance: redirecting the user to GitHub and exchanging the returned code for a session token.

**`GET /oauth/authorize`**
Redirects the browser to GitHub's OAuth authorization URL with `client_id`, `redirect_uri`, and `scope=read:user`. Generates and includes a `state` parameter (random UUID) stored in memory to prevent CSRF.

**`GET /oauth/callback?code=...&state=...`**
1. Validates `state` matches what was stored.
2. Exchanges `code` for a GitHub access token via `POST https://github.com/login/oauth/access_token`.
3. Fetches the GitHub username via `GET https://api.github.com/user` using the GitHub token.
4. Discards the GitHub token — it is never stored.
5. Generates a UUID opaque session token, stores `{ opaque_uuid: { github_username, created_at } }` in an in-memory dict.
6. Returns a JSON response `{ "token": "<opaque_uuid>", "user": "<github_username>" }` so the MCP client can extract and store the token.

The in-memory token store must expose a `lookup(token: str) -> dict | None` function used by the middleware in Issue 4.

## Acceptance criteria

- [ ] `GET /oauth/authorize` redirects to `https://github.com/login/oauth/authorize` with correct query params
- [ ] `GET /oauth/authorize` generates and stores a `state` value; mismatched state on callback returns 400
- [ ] `GET /oauth/callback` exchanges code for GitHub token (mocked in tests)
- [ ] GitHub access token is not stored anywhere after the user info fetch
- [ ] Callback response contains `token` (opaque UUID) and `user` (GitHub username)
- [ ] `lookup(token)` returns user info for a valid token and `None` for an unknown token
- [ ] Unit tests cover: successful flow, state mismatch, GitHub API error during token exchange

## Blocked by

Issue 1 — project scaffolding must exist first.
