# Issue 2: Weather Tools

## What to build

Implement the 3 MCP tools backed by Open-Meteo API (no API key required). Each tool must be registered with FastMCP, return structured text on success, and return a descriptive error string on failure — never raise an unhandled exception.

**`get_current_weather(lat: float, lon: float)`**
Calls Open-Meteo `/v1/forecast` with `current` fields: temperature, wind speed, weather code. Returns a human-readable summary.

**`get_forecast(lat: float, lon: float, days: int)`**
Calls Open-Meteo `/v1/forecast` with `daily` fields for up to 16 days. Returns a list of daily summaries. Validates that `days` is between 1 and 16.

**`get_weather_by_city(city: str)`**
Calls Open-Meteo Geocoding API (`/v1/search`) to resolve city name → (lat, lon), then calls the same forecast endpoint as `get_current_weather`. Returns an error string if the city is not found.

All tools must:
- Use `httpx` with a timeout (10s)
- Catch `httpx.HTTPError` and `httpx.TimeoutException` and return a descriptive error string
- Return an error string if Open-Meteo responds with a non-200 status

Unit tests mock all `httpx` calls and verify:
- Correct fields are extracted from a mocked successful response
- A network error returns a descriptive error string (not an exception)
- `get_forecast` rejects `days < 1` or `days > 16`
- `get_weather_by_city` returns an error string when geocoding returns zero results

## Acceptance criteria

- [ ] `tools/weather.py` implements all 3 tools registered with FastMCP
- [ ] Each tool returns a non-empty string on success with temperature and at least one other field
- [ ] Each tool returns a descriptive error string (not raises) on HTTP failure or timeout
- [ ] `get_forecast` validates `days` range and returns an error string if out of bounds
- [ ] `get_weather_by_city` returns an error if city not found in geocoding results
- [ ] Unit tests exist for all 3 tools covering success and failure paths, with httpx mocked

## Blocked by

Issue 1 — project scaffolding must exist first.
