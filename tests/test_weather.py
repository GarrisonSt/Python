import pytest
import requests

import weather


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def test_get_current_weather_normalizes_provider_data(monkeypatch):
    responses = [
        FakeResponse(
            {
                "results": [
                    {
                        "name": "Paris",
                        "admin1": "Ile-de-France",
                        "country": "France",
                        "latitude": 48.85,
                        "longitude": 2.35,
                    }
                ]
            }
        ),
        FakeResponse(
            {
                "current": {
                    "temperature_2m": 18.4,
                    "relative_humidity_2m": 62,
                    "apparent_temperature": 17.9,
                    "weather_code": 2,
                    "wind_speed_10m": 12.1,
                }
            }
        ),
    ]
    monkeypatch.setattr(weather.requests, "get", lambda *args, **kwargs: responses.pop(0))

    result = weather.get_current_weather("  Paris  ")

    assert result == {
        "city": "Paris",
        "region": "Ile-de-France",
        "country": "France",
        "temperature": 18.4,
        "feels_like": 17.9,
        "humidity": 62,
        "wind_speed": 12.1,
        "description": "Partly cloudy",
        "icon": "cloud-sun",
    }


def test_get_current_weather_requests_geocoding_and_current_conditions(monkeypatch):
    responses = [
        FakeResponse({"results": [{"name": "Oslo", "latitude": 59.91, "longitude": 10.75}]}),
        FakeResponse(
            {
                "current": {
                    "temperature_2m": 4,
                    "relative_humidity_2m": 70,
                    "apparent_temperature": 1,
                    "weather_code": 0,
                    "wind_speed_10m": 9,
                }
            }
        ),
    ]
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return responses.pop(0)

    monkeypatch.setattr(weather.requests, "get", fake_get)
    weather.get_current_weather("Oslo")

    assert calls[0][0] == weather.GEOCODING_URL
    assert calls[0][1]["params"]["name"] == "Oslo"
    assert calls[1][0] == weather.FORECAST_URL
    assert calls[1][1]["params"]["timezone"] == "auto"
    assert calls[1][1]["params"]["temperature_unit"] == "celsius"


def test_get_current_weather_raises_for_unknown_city(monkeypatch):
    monkeypatch.setattr(weather.requests, "get", lambda *args, **kwargs: FakeResponse({"results": []}))

    with pytest.raises(weather.CityNotFoundError):
        weather.get_current_weather("Atlantis")


def test_get_current_weather_rejects_blank_city():
    with pytest.raises(ValueError, match="blank"):
        weather.get_current_weather("  ")


def test_get_current_weather_wraps_provider_outage(monkeypatch):
    def fail(*args, **kwargs):
        raise requests.Timeout

    monkeypatch.setattr(weather.requests, "get", fail)

    with pytest.raises(weather.WeatherServiceError):
        weather.get_current_weather("Oslo")


def test_unknown_weather_code_uses_fallback_icon():
    assert weather.describe_weather_code(999) == ("Unknown conditions", "cloud")