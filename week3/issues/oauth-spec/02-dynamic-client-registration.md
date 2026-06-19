# Issue 2: Dynamic Client Registration

## What to build

Implement `POST /register` so Claude CLI can automatically register itself with the MCP server and receive a `client_id` without any manual configuration. This eliminates the need for `--client-id` flag when running `claude mcp add`.

**Behavior:**
- Claude CLI sends a registration request with its metadata (name, redirect URIs)
- Server generates a UUID `client_id`, stores `{client_id: {redirect_uris, client_name, registered_at}}` in an in-memory client store
- Server returns `client_id` (no `client_secret` — Claude CLI is a public client)
- Re-registration with the same redirect URIs is allowed and returns a new `client_id`

**Request shape (from Claude CLI):**
```json
{
  "client_name": "Claude CLI",
  "redirect_uris": ["http://localhost:54321/callback"],
  "grant_types": ["authorization_code"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "none"
}
```

**Response shape:**
```json
{
  "client_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "client_name": "Claude CLI",
  "redirect_uris": ["http://localhost:54321/callback"]
}
```

The endpoint must be public (no Bearer token required). The `registration_endpoint` field added in Issue 1's authorization server metadata must point to this endpoint.

## Acceptance criteria

- [ ] `POST /register` returns 200 with a `client_id` UUID
- [ ] The returned `client_id` is stored and retrievable for validation in later issues
- [ ] Requests without `redirect_uris` return 400
- [ ] The endpoint is in the middleware bypass list (no auth required)
- [ ] Tests cover: successful registration returns client_id; missing redirect_uris returns 400; registered client_id is findable in the store

## Blocked by

Issue 1 — discovery metadata must point to the registration endpoint.
