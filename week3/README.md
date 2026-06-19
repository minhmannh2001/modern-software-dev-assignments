# Week 3 — Remote HTTP MCP Weather Server

A remote MCP server that exposes 3 weather tools backed by the [Open-Meteo](https://open-meteo.com/) API (no API key required). Runs over HTTP (Streamable HTTP transport) and requires GitHub OAuth authentication before any tool can be called.

## Overview

- **Transport**: Streamable HTTP — MCP tools are available at `POST /mcp`
- **Auth**: GitHub OAuth 2.0 Authorization Code flow. After login, you receive an opaque session token to include as `Authorization: Bearer <token>` on all requests.
- **Tools**: `get_current_weather`, `get_forecast`, `get_weather_by_city`
- **Data source**: Open-Meteo API — free, no registration needed

## Prerequisites

- Python 3.10+
- A GitHub account (to create an OAuth App)

## GitHub OAuth App Setup

1. Go to [github.com/settings/developers](https://github.com/settings/developers)
2. Click **New OAuth App**
3. Fill in:
   - **Application name**: anything (e.g. `MCP Weather Server`)
   - **Homepage URL**: `http://localhost:8000`
   - **Authorization callback URL**: `http://localhost:8000/oauth/callback`
4. Click **Register application**
5. Copy the **Client ID** and generate a **Client Secret** — you'll need both in the next step

## Environment Setup

```bash
cd week3
cp .env.example .env
```

Edit `.env` and fill in your GitHub values:

```
GITHUB_CLIENT_ID=your_client_id_here
GITHUB_CLIENT_SECRET=your_client_secret_here
REDIRECT_URI=http://localhost:8000/oauth/callback
PORT=8000
```

## Install Dependencies

```bash
cd week3
pip install -r requirements.txt
```

## Running the Server

```bash
cd week3
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Authentication Flow

The server implements the [MCP Authorization Spec](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization) (OAuth 2.1 + PKCE). Spec-compliant MCP clients like Claude Code CLI handle the entire OAuth dance automatically — no manual token management needed.

**How it works under the hood:**
1. Claude CLI connects to the server → receives `401` with `WWW-Authenticate` header
2. Claude CLI fetches `/.well-known/oauth-protected-resource` and `/.well-known/oauth-authorization-server` to discover OAuth endpoints
3. Claude CLI registers itself via `POST /register` (Dynamic Client Registration)
4. Claude CLI opens a browser → you log in with GitHub → server redirects back to Claude CLI with an authorization code
5. Claude CLI exchanges the code for a bearer token via `POST /oauth/token` (PKCE-verified)
6. Claude CLI stores the token and uses it automatically on all subsequent requests

**Manual flow (for MCP Inspector or testing):**

1. Open a browser and visit: `http://localhost:8000/oauth/authorize?client_id=manual&redirect_uri=http://localhost:8000/oauth/callback&code_challenge=abc&code_challenge_method=S256&state=test`
2. You'll be redirected to GitHub — authorize the app
3. GitHub redirects back; the server redirects to the callback URL with `?code=<auth_code>`
4. Exchange the code at `POST /oauth/token` with your `code_verifier`

## Connecting with MCP Inspector

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) does not implement the MCP Authorization Spec, so you need to supply a Bearer token manually.

```bash
npx @modelcontextprotocol/inspector
```

In the Inspector UI:
1. Set **Transport** to `Streamable HTTP`
2. Set **URL** to `http://localhost:8000/mcp`
3. Add a custom header: `Authorization: Bearer <your-token>` (obtained via the manual flow above)
4. Click **Connect** — you should see the 3 weather tools listed

## Tool Reference

### `get_current_weather`

Returns current weather conditions at a geographic coordinate.

| Parameter | Type | Description |
|-----------|------|-------------|
| `lat` | float | Latitude (e.g. `48.85`) |
| `lon` | float | Longitude (e.g. `2.35`) |

**Example input:**
```json
{ "lat": 48.85, "lon": 2.35 }
```

**Example output:**
```
Temperature: 18.4°C, Wind speed: 12.1 km/h, Weather code: 2
```

**Errors:** Returns a descriptive string if Open-Meteo is unreachable or times out.

---

### `get_forecast`

Returns a daily weather forecast for up to 16 days.

| Parameter | Type | Description |
|-----------|------|-------------|
| `lat` | float | Latitude |
| `lon` | float | Longitude |
| `days` | int | Number of days to forecast (1–16) |

**Example input:**
```json
{ "lat": 48.85, "lon": 2.35, "days": 3 }
```

**Example output:**
```
2024-06-18: max 22.0°C, min 14.0°C, code 1
2024-06-19: max 19.5°C, min 13.0°C, code 3
2024-06-20: max 21.0°C, min 15.0°C, code 0
```

**Errors:** Returns an error string if `days` is outside 1–16, or if Open-Meteo is unreachable.

---

### `get_weather_by_city`

Resolves a city name to coordinates, then returns current weather.

| Parameter | Type | Description |
|-----------|------|-------------|
| `city` | str | City name (e.g. `"Hanoi"`) |

**Example input:**
```json
{ "city": "Hanoi" }
```

**Example output:**
```
Temperature: 31.2°C, Wind speed: 8.5 km/h, Weather code: 95
```

**Errors:** Returns an error string if the city is not found or Open-Meteo is unreachable.

## Connecting with Claude Code CLI

Register the server once — Claude CLI handles OAuth automatically:

```bash
claude mcp add --transport http weather http://localhost:8000/mcp -s project
```

On first use, Claude CLI will:
1. Detect the 401 response and discover the OAuth endpoints automatically
2. Register itself with the server
3. Open a browser for GitHub login
4. Exchange the authorization code for a token — stored securely in the system keychain

Verify the server is connected:

```bash
claude mcp list
```

You should see `weather: http://localhost:8000/mcp (HTTP) - ✔ Connected`.

Start a Claude session and ask about the weather:

```
What is the weather in Hanoi right now?
```

> **Note on server restarts:** Tokens are stored in memory and lost on server restart. When the server restarts, your stored token becomes invalid (401). Claude CLI will automatically re-trigger the browser login flow on the next request — no manual steps needed.

## Running Tests

```bash
cd week3
python -m pytest tests/ -v
```

Tests use mocked HTTP calls — no running server or real API keys needed.
