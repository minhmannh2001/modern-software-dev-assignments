# Issue 4: Bearer Token Middleware

## What to build

Implement a Starlette middleware in `auth.py` that enforces authentication on all MCP routes. OAuth routes remain publicly accessible.

**Behaviour:**
- Requests to `/oauth/authorize` and `/oauth/callback` pass through unconditionally.
- All other requests must include `Authorization: Bearer <opaque_uuid>`.
- The middleware extracts the token, calls `lookup(token)` from the token store (Issue 3), and:
  - If found: attaches user info to `request.state.user` and calls `next(request)`.
  - If missing or unknown: returns HTTP 401 with JSON `{ "error": "unauthorized" }`.

The middleware must not leak information about whether a token exists vs. is malformed — both cases return the same 401 response.

## Acceptance criteria

- [ ] Requests to `/oauth/authorize` and `/oauth/callback` return the route's response, not 401
- [ ] A request with a valid Bearer token reaches the downstream handler and has `request.state.user` populated
- [ ] A request with an unknown Bearer token returns 401 JSON
- [ ] A request with no `Authorization` header returns 401 JSON
- [ ] A malformed header (e.g., `Bearer` with no token) returns 401 JSON
- [ ] Unit tests cover all four cases above using a test Starlette app with the middleware applied

## Blocked by

Issue 3 — token store (`lookup`) must exist before middleware can use it.
