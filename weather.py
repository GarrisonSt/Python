import requests


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 10

WEATHER_CODES = {
    0: ("Clear sky", "sun"),
    1: ("Mainly clear", "cloud-sun"),
    2: ("Partly cloudy", "cloud-sun"),
    3: ("Overcast", "cloud"),
    45: ("Fog", "cloud"),
    48: ("Depositing rime fog", "cloud"),
    51: ("Light drizzle", "cloud-drizzle"),
    53: ("Moderate drizzle", "cloud-drizzle"),
    55: ("Dense drizzle", "cloud-drizzle"),
    56: ("Light freezing drizzle", "cloud-drizzle"),
    57: ("Dense freezing drizzle", "cloud-drizzle"),
    61: ("Slight rain", "cloud-rain"),
    63: ("Moderate rain", "cloud-rain"),
    65: ("Heavy rain", "cloud-rain"),
    66: ("Light freezing rain", "cloud-rain"),
    67: ("Heavy freezing rain", "cloud-rain"),
    71: ("Slight snow", "cloud-snow"),
    73: ("Moderate snow", "cloud-snow"),
    75: ("Heavy snow", "cloud-snow"),
    77: ("Snow grains", "cloud-snow"),
    80: ("Slight rain showers", "cloud-rain"),
    81: ("Moderate rain showers", "cloud-rain"),
    82: ("Violent rain showers", "cloud-rain"),
    85: ("Slight snow showers", "cloud-snow"),
    86: ("Heavy snow showers", "cloud-snow"),
    95: ("Thunderstorm", "cloud-lightning"),
    96: ("Thunderstorm with slight hail", "cloud-lightning"),
    99: ("Thunderstorm with heavy hail", "cloud-lightning"),
}


class WeatherServiceError(Exception):
    """Raised when the weather provider cannot return usable data."""


class CityNotFoundError(WeatherServiceError):
    """Raised when the geocoding service cannot find the requested city."""


def describe_weather_code(code):
    return WEATHER_CODES.get(code, ("Unknown conditions", "cloud"))


def _get_json(url, params):
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise WeatherServiceError("The weather provider returned an error.") from exc

    if not isinstance(payload, dict):
        raise WeatherServiceError("The weather provider returned invalid data.")
    return payload


def get_current_weather(city):
    city = city.strip()
    if not city:
        raise ValueError("City name cannot be blank.")

    geocoding = _get_json(
        GEOCODING_URL,
        {"name": city, "count": 1, "language": "en", "format": "json"},
    )
    results = geocoding.get("results")
    if not isinstance(results, list) or not results:
        raise CityNotFoundError(city)

    location = results[0]
    if not isinstance(location, dict) or "latitude" not in location or "longitude" not in location:
        raise WeatherServiceError("The geocoding service returned invalid location data.")

    conditions = _get_json(
        FORECAST_URL,
        {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": (
                "temperature_2m,relative_humidity_2m,apparent_temperature,"
                "weather_code,wind_speed_10m"
            ),
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "timezone": "auto",
        },
    )
    current = conditions.get("current")
    required_fields = (
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "weather_code",
        "wind_speed_10m",
    )
    if not isinstance(current, dict) or any(field not in current for field in required_fields):
        raise WeatherServiceError("The forecast service returned incomplete current conditions.")

    description, icon = describe_weather_code(current["weather_code"])
    return {
        "city": location.get("name", city),
        "region": location.get("admin1"),
        "country": location.get("country"),
        "temperature": current["temperature_2m"],
        "feels_like": current["apparent_temperature"],
        "humidity": current["relative_humidity_2m"],
        "wind_speed": current["wind_speed_10m"],
        "description": description,
        "icon": icon,
    }