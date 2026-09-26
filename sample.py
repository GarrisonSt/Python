from flask import Flask, render_template, request
import weather

app = Flask(__name__)


def get_current_weather(city):
    return weather.get_current_weather(city)


@app.get("/")
def index():
    city = request.args.get("city", "").strip()
    current_weather = None
    error = None

    if "city" in request.args:
        if not city:
            error = "Enter a city name to search."
        else:
            try:
                current_weather = get_current_weather(city)
            except weather.CityNotFoundError:
                error = f"We couldn't find a city named {city}. Check the spelling and try again."
            except weather.WeatherServiceError:
                error = "Weather data is temporarily unavailable. Please try again."

    return render_template(
        "index.html", city=city, weather=current_weather, error=error
    )


if __name__ == "__main__":
    app.run(debug=True)
