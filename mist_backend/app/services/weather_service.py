import httpx

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Common WMO weather codes, condensed to plain language for her replies.
_WEATHER_CODES = {
    0: "clear sky",
    1: "mostly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    48: "foggy with frost",
    51: "light drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "light snow",
    73: "moderate snow",
    75: "heavy snow",
    80: "rain showers",
    95: "thunderstorm",
}


def get_weather(location: str) -> dict:
    with httpx.Client(timeout=10) as client:
        geo_resp = client.get(_GEOCODE_URL, params={"name": location, "count": 1})
        geo_resp.raise_for_status()
        results = geo_resp.json().get("results")
        if not results:
            return {"error": f"Could not find a location matching '{location}'."}

        place = results[0]
        forecast_resp = client.get(
            _FORECAST_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "timezone": "auto",
            },
        )
        forecast_resp.raise_for_status()
        current = forecast_resp.json().get("current", {})

    code = current.get("weather_code")
    return {
        "location": f"{place.get('name')}, {place.get('country', '')}".strip(", "),
        "condition": _WEATHER_CODES.get(code, "unknown conditions"),
        "temperature_c": current.get("temperature_2m"),
        "humidity_percent": current.get("relative_humidity_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
    }
