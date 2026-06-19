# Issue 4: Token Endpoint

## What to build

Implement `POST /oauth/token` — the endpoint where Claude CLI exchanges the authorization code (received in Issue 3) for a bearer token it can use on all subsequent MCP requests.

**Request (from Claude CLI, form-encoded):**
```
grant_type=authorization_code
code=<auth_code from Issue 3>
code_verifier=<the original random secret>
redirect_uri=http://localhost:54321/callback
client_id=<registered client_id>
```

**Validation steps (in order):**
1. `grant_type` must be `authorization_code`
2. `code` must exist in the authorization code store
3. `code` must not be expired (5-minute TTL)
4. `client_id` must match what was stored with the code
5. `redirect_uri` must match what was stored with the code
6. PKCE check: `BASE64URL(SHA256(code_verifier))` must equal the stored `code_challenge`
7. Mark the code as used (single-use — delete it from store after first exchange)

**On success:**
- Generate a UUID opaque bearer token
- Store it in the existing token store: `{opaque_token → {github_username, created_at}}`
- Delete the authorization code from the store (single-use)
- Return:
  ```json
  {
    "access_token": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "token_type": "Bearer"
  }
  ```

**On failure:** return 400 with a descriptive error string.

The endpoint must be public (no Bearer token required). After this issue, Claude CLI can complete the full OAuth flow autonomously.

## Acceptance criteria

- [ ] Valid `code` + correct `code_verifier` returns 200 with `access_token`
- [ ] The returned `access_token` is accepted by `BearerTokenMiddleware` on subsequent MCP requests
- [ ] Wrong `code_verifier` returns 400
- [ ] Expired authorization code (older than 5 minutes) returns 400
- [ ] Same `code` used twice: first returns 200, second returns 400 (single-use)
- [ ] Missing or mismatched `client_id` or `redirect_uri` returns 400
- [ ] The endpoint is in the middleware bypass list (no auth required)
- [ ] Tests cover all failure cases above plus the happy path end-to-end

## Blocked by

Issue 3 — authorization code store and PKCE params must exist before they can be verified here.
