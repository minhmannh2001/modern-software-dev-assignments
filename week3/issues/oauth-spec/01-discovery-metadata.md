# Issue 1: Discovery Metadata Endpoints + WWW-Authenticate Header

## What to build

Expose the two metadata endpoints required by the MCP Authorization Spec so that any spec-compliant MCP client (including Claude CLI) can automatically discover the authorization server. Also update the 401 response to include the `WWW-Authenticate` header that triggers the auto-discovery flow in MCP clients.

**Three deliverables end-to-end:**

1. `GET /.well-known/oauth-protected-resource` (public, no auth) — returns RFC9728 metadata indicating this server is a protected resource and naming its authorization server:
   ```json
   {
     "resource": "http://localhost:8000",
     "authorization_servers": ["http://localhost:8000"]
   }
   ```

2. `GET /.well-known/oauth-authorization-server` (public, no auth) — returns RFC8414 metadata so clients know all OAuth endpoints and capabilities:
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

3. **Update `BearerTokenMiddleware`** — 401 responses must include the `WWW-Authenticate` header so MCP clients know where to find the resource metadata:
   ```
   WWW-Authenticate: Bearer realm="MCP Weather Server",
     resource_metadata="http://localhost:8000/.well-known/oauth-protected-resource"
   ```

All three paths must be added to the middleware bypass list (no Bearer token required to access them).

The server URL (`http://localhost:8000`) must be read from config/env so it works on any port.

## Acceptance criteria

- [ ] `GET /.well-known/oauth-protected-resource` returns 200 with correct JSON (no auth required)
- [ ] `GET /.well-known/oauth-authorization-server` returns 200 with correct JSON including all five required fields
- [ ] `POST /mcp` without a token returns 401 with `WWW-Authenticate` header containing `resource_metadata` URL
- [ ] OAuth paths and new well-known paths all bypass the middleware (no 401)
- [ ] Tests cover: both metadata endpoints return correct shape; 401 response contains `WWW-Authenticate`

## Blocked by

None — can start immediately.
