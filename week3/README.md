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

Before calling any tool, you need a session token:

1. Open a browser and visit: `http://localhost:8000/oauth/authorize`
2. You'll be redirected to GitHub — authorize the app
3. GitHub redirects back to the server, which returns a JSON response:
   ```json
   { "token": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "user": "your-github-username" }
   ```
4. Copy the `token` value — use it as your Bearer token in all subsequent requests

## Connecting with MCP Inspector

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) lets you browse and call tools interactively.

```bash
npx @modelcontextprotocol/inspector
```

In the Inspector UI:
1. Set **Transport** to `Streamable HTTP`
2. Set **URL** to `http://localhost:8000/mcp`
3. Add a custom header: `Authorization: Bearer <your-token>` (from the auth step above)
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

After completing the [Authentication Flow](#authentication-flow) to get a session token, register the server with Claude Code:

```bash
claude mcp add --transport http weather http://localhost:8000/mcp \
  -H "Authorization: Bearer <your-token>" \
  -s project
```

Verify the server is connected:

```bash
claude mcp list
```

You should see `weather: http://localhost:8000/mcp (HTTP) - ✔ Connected`.

Start a Claude session and ask about the weather:

```
What is the weather in Hanoi right now?
```

Claude will automatically call `get_weather_by_city` and return the result.

> **Note:** The session token is stored in memory and is lost when the server restarts. After each server restart, repeat the Authentication Flow to get a new token, then re-add the server:
> ```bash
> claude mcp remove weather
> claude mcp add --transport http weather http://localhost:8000/mcp \
>   -H "Authorization: Bearer <new-token>" \
>   -s project
> ```

## Running Tests

```bash
cd week3
python -m pytest tests/ -v
```

Tests use mocked HTTP calls — no running server or real API keys needed.
