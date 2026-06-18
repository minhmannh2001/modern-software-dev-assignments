# PRD: Remote HTTP MCP Weather Server with GitHub OAuth

## Problem Statement

Developers need a working example of a remote MCP server that goes beyond the basic stdio pattern — specifically one that runs over HTTP, exposes real-world data tools, and enforces proper OAuth2 authentication so only authenticated users can invoke the tools.

## Solution

Build a remote HTTP MCP server (using FastMCP / official `mcp` SDK) that:
- Exposes 3 weather tools backed by the Open-Meteo API (no API key required)
- Requires clients to authenticate via GitHub OAuth (Authorization Code flow) before calling any tool
- Issues opaque session tokens after successful OAuth; never forwards the GitHub token to the upstream weather API
- Runs locally on HTTP so it can be tested with the MCP Inspector and called by any MCP-aware agent or client

## User Stories

1. As an MCP client, I want to initiate a GitHub OAuth flow through the MCP server so that I can authenticate without managing API keys manually.
2. As an MCP client, I want to receive an opaque session token after successful GitHub login so that I can include it as a Bearer token on all subsequent tool calls.
3. As an MCP client, I want unauthenticated requests to return 401 so that I know immediately when my token is missing or invalid.
4. As an MCP client, I want to call `get_current_weather` with a latitude and longitude so that I can retrieve real-time weather conditions at any location.
5. As an MCP client, I want to call `get_forecast` with a latitude, longitude, and number of days so that I can see weather predictions for upcoming days.
6. As an MCP client, I want to call `get_weather_by_city` with a city name so that I can get weather without knowing exact coordinates.
7. As an MCP client, I want tool errors (network failures, bad inputs, Open-Meteo timeouts) returned as structured error messages so that I can handle them gracefully.
8. As a developer, I want the server to run with a single command after setting two env vars so that setup is fast.
9. As a developer, I want a `.env.example` file listing all required environment variables so that I know exactly what to configure.
10. As a developer, I want the MCP Inspector to work against the local server so that I can debug tools interactively before integrating with an agent.
11. As a developer, I want a README with step-by-step instructions for creating the GitHub OAuth App and running the server so that the setup is reproducible.

## Implementation Decisions

- **Transport**: Streamable HTTP via `FastMCP` from the official `mcp` SDK. The same Starlette app hosts both MCP routes and OAuth routes.
- **Auth flow**: GitHub Authorization Code flow. The server exposes `/oauth/authorize` (redirects to GitHub) and `/oauth/callback` (exchanges code for GitHub access token, generates a UUID opaque token, stores in memory, redirects client back with the opaque token).
- **Token store**: In-memory dict `{ opaque_uuid: { github_username, created_at } }`. Resets on server restart. No persistent storage needed for this assignment.
- **GitHub token isolation**: The GitHub access token is used only to verify the user's identity at callback time (`GET https://api.github.com/user`). It is stored nowhere and never forwarded to Open-Meteo.
- **Request authentication**: A Starlette middleware extracts `Authorization: Bearer <opaque_uuid>`, looks it up in the token store, and rejects with 401 if absent or unknown. MCP tool routes are protected; OAuth routes are public.
- **Weather tools** (all backed by Open-Meteo API, no API key):
  - `get_current_weather(lat: float, lon: float)` → temperature, wind speed, weather code
  - `get_forecast(lat: float, lon: float, days: int)` → daily forecast array up to 16 days
  - `get_weather_by_city(city: str)` → calls Open-Meteo Geocoding API to resolve city → (lat, lon), then returns current weather
- **Error handling**: All tool functions catch `httpx` exceptions and return descriptive error strings rather than raising, so the MCP client receives a clean tool result even on failure.
- **Config**: `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `PORT` (default 8000), `REDIRECT_URI` loaded from environment / `.env`.
- **Modules**:
  - `config.py` — loads and validates env vars at startup
  - `auth.py` — OAuth routes, token store, Bearer validation middleware
  - `tools/weather.py` — 3 tool definitions registered with FastMCP
  - `main.py` — wires everything together, starts the server

## Testing Decisions

Good tests verify external behavior through the module's public interface, not internal implementation. They should survive internal refactors.

- **`tools/weather.py`**: mock `httpx` HTTP calls to Open-Meteo; assert that each tool returns expected fields on success and a descriptive error string on network failure or bad response.
- **`auth.py`**: test token generation (UUID returned), token validation (valid UUID → passes, unknown UUID → 401, missing header → 401), and that the GitHub token is not stored after the callback.
- **`main.py` integration**: use `TestClient` against the assembled Starlette app; verify that an unauthenticated request to an MCP endpoint returns 401, and an authenticated request reaches the tool layer.

## Out of Scope

- Persistent token storage (database, Redis)
- Token expiry / refresh
- Deployed remote server (Vercel, Cloudflare) — running locally is sufficient
- Rate limiting beyond a basic user-facing error message
- Multiple GitHub OAuth scopes beyond identity (`read:user`)
- PKCE extension to the Authorization Code flow

## Further Notes

- The GitHub OAuth App must be created at github.com/settings/developers with `Authorization callback URL` set to `http://localhost:{PORT}/oauth/callback`.
- Open-Meteo is free and requires no registration — the only credentials needed are the GitHub OAuth App client ID and secret.
- The MCP Inspector (`npx @modelcontextprotocol/inspector`) can be pointed at `http://localhost:{PORT}/mcp` to test tools interactively.
