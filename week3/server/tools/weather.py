import httpx

_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
_TIMEOUT = 10.0


def get_current_weather(lat: float, lon: float) -> str:
    try:
        resp = httpx.get(
            _FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,wind_speed_10m,weather_code",
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        current = resp.json()["current"]
        return (
            f"Temperature: {current['temperature_2m']}°C, "
            f"Wind speed: {current['wind_speed_10m']} km/h, "
            f"Weather code: {current['weather_code']}"
        )
    except httpx.TimeoutException:
        return "Error: request to Open-Meteo timed out."
    except httpx.HTTPError as e:
        return f"Error: HTTP request failed — {e}"


def get_forecast(lat: float, lon: float, days: int) -> str:
    if days < 1 or days > 16:
        return "Error: days must be between 1 and 16."
    try:
        resp = httpx.get(
            _FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,weather_code",
                "forecast_days": days,
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        daily = resp.json()["daily"]
        lines = []
        for i, date in enumerate(daily["time"]):
            lines.append(
                f"{date}: max {daily['temperature_2m_max'][i]}°C, "
                f"min {daily['temperature_2m_min'][i]}°C, "
                f"code {daily['weather_code'][i]}"
            )
        return "\n".join(lines)
    except httpx.TimeoutException:
        return "Error: request to Open-Meteo timed out."
    except httpx.HTTPError as e:
        return f"Error: HTTP request failed — {e}"


def get_weather_by_city(city: str) -> str:
    try:
        geo = httpx.get(
            _GEOCODING_URL,
            params={"name": city, "count": 1},
            timeout=_TIMEOUT,
        )
        geo.raise_for_status()
        results = geo.json().get("results", [])
        if not results:
            return f"Error: city '{city}' not found."
        lat = results[0]["latitude"]
        lon = results[0]["longitude"]
        return get_current_weather(lat=lat, lon=lon)
    except httpx.TimeoutException:
        return "Error: request to Open-Meteo timed out."
    except httpx.HTTPError as e:
        return f"Error: HTTP request failed — {e}"
