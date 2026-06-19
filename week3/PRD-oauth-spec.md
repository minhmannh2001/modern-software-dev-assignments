# PRD: MCP Authorization Spec — Automatic OAuth Flow for Claude CLI

## Problem Statement

Hiện tại, mỗi lần khởi động lại MCP server, token bị mất (lưu trong memory). Developer phải thủ công: vào browser → `/oauth/authorize` → copy token → chạy `claude mcp remove` → `claude mcp add` với token mới. Nếu server restart nhiều lần trong ngày, quy trình này lặp đi lặp lại và rất tốn thời gian.

Ngoài ra, Claude CLI không thể tự động khởi tạo OAuth flow vì server chưa implement MCP Authorization Spec — spec định nghĩa các metadata endpoint để MCP client tự discover và thực hiện toàn bộ OAuth dance mà không cần thao tác thủ công.

## Solution

Implement đầy đủ MCP Authorization Spec (dựa trên OAuth 2.1, RFC8414, RFC9728, RFC7591) trên MCP server. Sau đó Claude CLI sẽ:

1. Gửi request → nhận 401 với `WWW-Authenticate` header
2. Tự fetch metadata để discover authorization server
3. Tự mở browser → user đăng nhập GitHub một lần
4. Nhận authorization code → tự exchange lấy token
5. Lưu token vào macOS Keychain (tự refresh khi hết hạn)

Developer không cần thao tác thủ công nào sau lần đăng ký đầu tiên.

## User Stories

1. As a developer, I want Claude CLI to automatically open a browser for GitHub OAuth when the MCP server requires authentication, so that I don't have to manually copy-paste tokens.
2. As a developer, I want Claude CLI to store the OAuth token securely, so that I don't need to re-authenticate every time I start a new Claude session.
3. As a developer, I want the MCP server to return a proper `WWW-Authenticate` header on 401 responses, so that any spec-compliant MCP client can discover the auth flow automatically.
4. As a developer, I want the MCP server to expose a `/.well-known/oauth-protected-resource` endpoint, so that MCP clients can discover which authorization server to use.
5. As a developer, I want the MCP server to expose a `/.well-known/oauth-authorization-server` endpoint, so that MCP clients know the authorization endpoint, token endpoint, and supported capabilities.
6. As a developer, I want the authorization server to support Dynamic Client Registration (RFC7591), so that Claude CLI can register itself automatically without me pre-configuring a client_id.
7. As a developer, I want the authorization flow to use PKCE (Proof Key for Code Exchange), so that the flow is secure against authorization code interception.
8. As a developer, I want the server to issue its own opaque tokens (not GitHub tokens), so that GitHub credentials are never exposed to MCP clients.
9. As a developer, I want the token exchange to happen at a `/oauth/token` endpoint, so that Claude CLI can exchange an authorization code for a token programmatically.
10. As a developer, I want the authorization callback to redirect back to Claude CLI's local callback URL (not return JSON), so that the OAuth flow integrates correctly with Claude CLI's built-in callback handler.
11. As a developer, I want the server to validate the `resource` parameter in OAuth requests (RFC8707), so that tokens are audience-bound and cannot be misused across services.
12. As a developer, I want to run `claude mcp add --transport http weather http://localhost:8000/mcp` once and never need to manage tokens manually, so that the integration is seamless.

## Implementation Decisions

### Overview of changes

The current auth flow returns JSON to the browser at callback time. The spec-compliant flow must redirect back to the MCP client's callback URL with an authorization code, which the client then exchanges at a token endpoint. This requires significant refactoring of `auth.py` and new endpoints.

### New endpoints required

**Protected Resource Metadata** (`GET /.well-known/oauth-protected-resource`):
- Public (no auth required)
- Returns JSON per RFC9728:
  ```json
  {
    "resource": "http://localhost:8000",
    "authorization_servers": ["http://localhost:8000"]
  }
  ```

**Authorization Server Metadata** (`GET /.well-known/oauth-authorization-server`):
- Public (no auth required)
- Returns JSON per RFC8414:
  ```json
  {
    "issuer": "http://localhost:8000",
    "authorization_endpoint": "http://localhost:8000/oauth/authorize",
    "token_endpoint": "http://localhost:8000/oauth/token",
    "registration_endpoint": "http://localhost:8000/register",
    "response_types_supported": ["code"],
    "grant_types_supported": ["authorization_code"],
    "code_challenge_methods_supported": ["S256"]
  }
  ```

**Dynamic Client Registration** (`POST /register`):
- Public (no auth required)
- Accepts any registration request from Claude CLI
- Generates and returns a `client_id` (UUID)
- Stores client metadata (redirect URIs) in memory
- Does not issue a `client_secret` (Claude CLI is a public client)

**Token Endpoint** (`POST /oauth/token`):
- Public (no auth required, protected by PKCE)
- Accepts `grant_type=authorization_code`, `code`, `code_verifier`, `redirect_uri`, `client_id`
- Validates PKCE: `BASE64URL(SHA256(code_verifier))` must equal stored `code_challenge`
- Validates `code` is not expired (TTL: 5 minutes)
- Returns `{"access_token": "<opaque-uuid>", "token_type": "Bearer"}`
- Discards the authorization code after use (single-use)

### Changes to existing endpoints

**`GET /oauth/authorize`** — significant update:
- Now accepts: `client_id`, `redirect_uri`, `response_type=code`, `state`, `code_challenge`, `code_challenge_method=S256`, `resource`
- Validates `client_id` exists in the registered clients store
- Validates `redirect_uri` matches what was registered
- Stores `{state, code_challenge, code_challenge_method, redirect_uri, client_id}` in a pending authorization store (keyed by the internal GitHub OAuth state)
- Continues to redirect user to GitHub OAuth (as before), but carries extra context through the flow

**`GET /oauth/callback`** (GitHub callback) — significant update:
- After exchanging GitHub code for user identity (same as before)
- Generates a short-lived authorization code (UUID, TTL 5 minutes)
- Stores `{auth_code: {github_username, code_challenge, code_challenge_method, redirect_uri, client_id, expires_at}}` in an authorization code store
- **Redirects** to the client's `redirect_uri?code=<auth_code>&state=<original_state>` instead of returning JSON
- Does NOT return a token directly

**`BearerTokenMiddleware`** — update 401 response:
- Must include `WWW-Authenticate` header on 401:
  ```
  WWW-Authenticate: Bearer realm="MCP Weather Server",
    resource_metadata="http://localhost:8000/.well-known/oauth-protected-resource"
  ```
- Public paths bypass list expands to include: `/.well-known/oauth-protected-resource`, `/.well-known/oauth-authorization-server`, `/register`, `/oauth/token`

### In-memory stores (all reset on server restart)

- **Registered clients store**: `{client_id: {redirect_uris: [...], registered_at}}`
- **Pending authorizations store**: `{github_state: {code_challenge, code_challenge_method, redirect_uri, client_id, mcp_state}}` — keyed by the GitHub OAuth state UUID
- **Authorization code store**: `{auth_code: {github_username, code_challenge, redirect_uri, client_id, expires_at}}` — single-use, 5-minute TTL
- **Token store** (existing): `{opaque_token: {github_username, created_at}}` — no expiry (reset on restart)

### Config

`REDIRECT_URI` env var is no longer used as the OAuth callback registered with GitHub. The GitHub OAuth App's callback URL remains `http://localhost:8000/oauth/callback` (fixed). Client-provided `redirect_uri` (from Claude CLI) is validated against the client's registered URIs.

## Testing Decisions

Good tests verify external behavior through public interfaces — what the endpoint returns, not how it generates it internally. Tests should survive internal refactors (e.g., changing the token generation algorithm) as long as the HTTP contract is preserved.

**Modules to test:**

- **Protected Resource Metadata endpoint**: assert response contains `resource` and `authorization_servers` fields pointing to localhost:8000
- **Authorization Server Metadata endpoint**: assert response contains `authorization_endpoint`, `token_endpoint`, `registration_endpoint`, `code_challenge_methods_supported: ["S256"]`
- **Dynamic Client Registration**: assert POST returns `client_id`; assert duplicate redirect_uri on re-registration returns same or new `client_id`
- **Token endpoint — success**: assert valid `code` + correct `code_verifier` returns `access_token`
- **Token endpoint — PKCE failure**: assert wrong `code_verifier` returns 400
- **Token endpoint — expired code**: assert code older than 5 minutes returns 400
- **Token endpoint — double use**: assert same code used twice returns 400 on second use
- **401 response**: assert `WWW-Authenticate` header is present and contains `resource_metadata` URL
- **`/oauth/authorize` redirects to GitHub** with correct params including client_id and state
- **`/oauth/callback` redirects to client redirect_uri** with `code` and `state` params (mock GitHub API calls)

**Prior art**: existing `test_auth.py` uses `TestClient` + monkeypatched module-level stores + `patch` for GitHub HTTP calls — same pattern applies to new endpoints.

## Out of Scope

- Refresh tokens (token validity resets on server restart anyway)
- Token expiry (tokens live until server restart)
- HTTPS (running locally only; spec requires HTTPS for production)
- Multiple authorization servers
- Persistent storage of registered clients or tokens across restarts
- Revoking tokens
- OpenID Connect / userinfo endpoint

## Further Notes

- Claude CLI uses `--callback-port` to fix the OAuth callback port. Without this, it picks a random port, which cannot be pre-registered. For local testing, the user should use `claude mcp add --transport http --callback-port 54321 weather http://localhost:8000/mcp` and register `http://localhost:54321/callback` as an allowed redirect URI during Dynamic Client Registration — the registration endpoint should store whatever redirect URI the client sends without validation (trust the client).
- The GitHub OAuth App's **Authorization callback URL** remains fixed at `http://localhost:8000/oauth/callback`. This is the server-to-GitHub callback, not the MCP client callback.
- After this implementation, `claude mcp add --transport http weather http://localhost:8000/mcp -s project` is sufficient. Claude CLI will handle the rest automatically on first use.
