from unittest.mock import MagicMock, patch

import httpx
import pytest

from server.tools.weather import get_current_weather, get_forecast, get_weather_by_city

_PATCH = "server.tools.weather.httpx.get"


def _ok(json_data: dict) -> MagicMock:
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = json_data
    mock.raise_for_status.return_value = None
    return mock


_CURRENT_RESPONSE = {
    "current": {
        "temperature_2m": 22.5,
        "wind_speed_10m": 14.3,
        "weather_code": 1,
    }
}


def test_get_current_weather_returns_temperature_and_wind():
    with patch(_PATCH, return_value=_ok(_CURRENT_RESPONSE)):
        result = get_current_weather(lat=10.0, lon=20.0)
    assert "22.5" in result
    assert "14.3" in result


def test_get_current_weather_http_error_returns_error_string():
    with patch(_PATCH, side_effect=httpx.HTTPError("connection refused")):
        result = get_current_weather(lat=10.0, lon=20.0)
    assert "Error" in result


def test_get_current_weather_timeout_returns_error_string():
    with patch(_PATCH, side_effect=httpx.TimeoutException("timed out")):
        result = get_current_weather(lat=10.0, lon=20.0)
    assert "timed out" in result.lower() or "Error" in result


# --- get_forecast ---

_FORECAST_RESPONSE = {
    "daily": {
        "time": ["2024-01-01", "2024-01-02"],
        "temperature_2m_max": [25.0, 23.0],
        "temperature_2m_min": [15.0, 13.0],
        "weather_code": [1, 3],
    }
}


def test_get_forecast_days_too_low_returns_error():
    with patch(_PATCH) as mock:
        result = get_forecast(lat=10.0, lon=20.0, days=0)
        mock.assert_not_called()
    assert "Error" in result


def test_get_forecast_days_too_high_returns_error():
    with patch(_PATCH) as mock:
        result = get_forecast(lat=10.0, lon=20.0, days=17)
        mock.assert_not_called()
    assert "Error" in result


def test_get_forecast_success_returns_daily_summaries():
    with patch(_PATCH, return_value=_ok(_FORECAST_RESPONSE)):
        result = get_forecast(lat=10.0, lon=20.0, days=2)
    assert "2024-01-01" in result
    assert "25.0" in result
    assert "2024-01-02" in result


def test_get_forecast_http_error_returns_error_string():
    with patch(_PATCH, side_effect=httpx.HTTPError("bad gateway")):
        result = get_forecast(lat=10.0, lon=20.0, days=3)
    assert "Error" in result


# --- get_weather_by_city ---

_GEO_NOT_FOUND = {"results": []}
_GEO_FOUND = {"results": [{"latitude": 48.85, "longitude": 2.35}]}


def test_get_weather_by_city_not_found_returns_error():
    with patch(_PATCH, return_value=_ok(_GEO_NOT_FOUND)):
        result = get_weather_by_city("Atlantis")
    assert "Error" in result
    assert "Atlantis" in result


def test_get_weather_by_city_success_returns_weather():
    with patch(_PATCH) as mock:
        mock.side_effect = [_ok(_GEO_FOUND), _ok(_CURRENT_RESPONSE)]
        result = get_weather_by_city("Paris")
    assert "22.5" in result
    assert "14.3" in result
