from liman_core.dishka import FromLiman
from services import LocationService

WEATHER_DATA: dict[str, tuple[float, str]] = {
    "london": (15.0, "cloudy"),
    "tokyo": (22.0, "sunny"),
    "moscow": (3.0, "snowy"),
    "barcelona": (24.0, "sunny"),
    "new york": (18.0, "partly cloudy"),
    "sydney": (26.0, "sunny"),
}


def get_weather(
    location_service: FromLiman[LocationService], location: str | None = None
) -> str:
    location_ = location or location_service.get_current()
    data = WEATHER_DATA.get(location_.lower())
    if not data:
        return f"No weather data for {location}."

    temp, condition = data
    return f"{location_}: {temp}°C, {condition}"
