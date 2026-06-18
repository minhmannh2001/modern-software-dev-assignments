# Issue 5: FastMCP HTTP Server Wiring

## What to build

Wire all components into a single runnable server in `main.py`. The result is a fully functional MCP server callable by any MCP-aware client or the MCP Inspector.

**What `main.py` does:**
1. Loads config via `config.py` (fails fast if env vars missing).
2. Creates a `FastMCP` instance and registers the 3 weather tools from `tools/weather.py`.
3. Gets the underlying Starlette app from FastMCP (Streamable HTTP transport).
4. Mounts the OAuth routes (`/oauth/authorize`, `/oauth/callback`) from `auth.py` onto the same Starlette app.
5. Wraps the app with the Bearer token middleware from `auth.py`.
6. Exposes the app as `app` for uvicorn: `uvicorn server.main:app --host 0.0.0.0 --port $PORT`.

The MCP tools endpoint must be reachable at `/mcp` (FastMCP default for Streamable HTTP).

Integration test using `TestClient`:
- Unauthenticated request to `/mcp` → 401
- Authenticated request (valid UUID in token store) reaches the MCP layer (200 or MCP-level response)

## Acceptance criteria

- [ ] `uvicorn server.main:app` starts without errors when `.env` is correctly populated
- [ ] `GET /oauth/authorize` is reachable without a token (returns redirect)
- [ ] `POST /mcp` without a token returns 401
- [ ] MCP Inspector (`npx @modelcontextprotocol/inspector`) can connect to `http://localhost:8000/mcp` after completing the OAuth flow and setting the Bearer token
- [ ] All 3 tools are visible and invocable in the MCP Inspector
- [ ] Integration test verifies 401 on unauthenticated MCP request

## Blocked by

Issue 2 — weather tools, Issue 3 — OAuth flow, Issue 4 — middleware.
