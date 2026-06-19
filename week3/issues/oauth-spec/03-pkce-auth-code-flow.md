# Issue 3: PKCE-Aware Authorization Code Flow

## What to build

Refactor the existing `/oauth/authorize` and `/oauth/callback` endpoints so the flow is PKCE-compliant and redirects the authorization code back to Claude CLI rather than returning a JSON token directly to the browser.

**Current behavior (broken for MCP clients):**
- `/oauth/callback` returns `{"token": "...", "user": "..."}` as JSON to the browser
- Claude CLI never receives the token because it's not watching the browser

**New behavior:**
- `/oauth/authorize` accepts PKCE params (`code_challenge`, `code_challenge_method=S256`), `client_id`, and `redirect_uri` from Claude CLI
- Validates `client_id` exists in the registered clients store (from Issue 2)
- Validates `redirect_uri` matches one registered for that `client_id`
- Stores `{github_state → {code_challenge, redirect_uri, client_id, mcp_state}}` in a pending authorization store, then redirects to GitHub as before
- `/oauth/callback` (GitHub's redirect target) continues to exchange the GitHub code for user identity as before, then:
  - Generates a short-lived authorization code (UUID, 5-minute TTL, single-use)
  - Stores `{auth_code → {github_username, code_challenge, redirect_uri, client_id, expires_at}}` in an authorization code store
  - **Redirects to client's `redirect_uri`** with `?code=<auth_code>&state=<mcp_state>` — NOT returns JSON

Claude CLI is now listening at its `redirect_uri` and receives the authorization code to exchange in Issue 4.

**New in-memory stores:**
- Pending authorizations: `{github_state → {code_challenge, redirect_uri, client_id, mcp_state}}`
- Authorization codes: `{auth_code → {github_username, code_challenge, redirect_uri, client_id, expires_at}}`

## Acceptance criteria

- [ ] `GET /oauth/authorize` with valid `client_id`, `redirect_uri`, `code_challenge`, `code_challenge_method=S256` redirects to GitHub (same as before)
- [ ] `GET /oauth/authorize` with unknown `client_id` returns 400
- [ ] `GET /oauth/authorize` with `redirect_uri` not matching the registered client returns 400
- [ ] `GET /oauth/callback` (after GitHub OAuth) redirects to `redirect_uri?code=<auth_code>&state=<state>` — no JSON response
- [ ] The authorization code is stored with the `code_challenge` for PKCE verification in Issue 4
- [ ] Tests cover: authorize validates client_id and redirect_uri; callback redirects to client (mock GitHub API calls); unknown state on callback returns 400

## Blocked by

Issue 2 — client store must exist for `client_id` validation.
