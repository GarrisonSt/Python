# Weather Desk

A small Flask app for current city weather, powered by Open-Meteo. No API key is required.

## Run locally

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python sample.py
```

Open <http://127.0.0.1:5001> and search for a city. Temperatures are shown in Celsius and wind speed in kilometers per hour.

## Tests

```sh
python -m pytest
```

The tests mock provider requests and do not require a network connection.