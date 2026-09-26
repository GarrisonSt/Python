import sample
import weather


def test_home_page_shows_search_form():
    response = sample.app.test_client().get("/")

    assert response.status_code == 200
    assert b' name="city"' in response.data
    assert b"Search a city to see its current conditions." in response.data


def test_search_shows_current_weather(monkeypatch):
    monkeypatch.setattr(
        sample,
        "get_current_weather",
        lambda city: {
            "city": city,
            "region": "Ontario",
            "country": "Canada",
            "temperature": 20,
            "feels_like": 19,
            "humidity": 55,
            "wind_speed": 8,
            "description": "Clear sky",
            "icon": "sun",
        },
    )

    response = sample.app.test_client().get("/?city=Toronto")

    assert response.status_code == 200
    assert b"Toronto" in response.data
    assert b"Ontario, Canada" in response.data
    assert b'data-lucide="sun"' in response.data
    assert b"Clear sky" in response.data


def test_search_shows_unknown_city_message(monkeypatch):
    def not_found(city):
        raise weather.CityNotFoundError(city)

    monkeypatch.setattr(sample, "get_current_weather", not_found)

    response = sample.app.test_client().get("/?city=Atlantis")

    assert response.status_code == 200
    assert b"city named Atlantis. Check the spelling" in response.data


def test_search_shows_provider_error_message(monkeypatch):
    def unavailable(city):
        raise weather.WeatherServiceError

    monkeypatch.setattr(sample, "get_current_weather", unavailable)

    response = sample.app.test_client().get("/?city=Oslo")

    assert response.status_code == 200
    assert b"Weather data is temporarily unavailable" in response.data


def test_blank_search_shows_validation_message():
    response = sample.app.test_client().get("/?city=%20%20")

    assert response.status_code == 200
    assert b"Enter a city name to search." in response.data