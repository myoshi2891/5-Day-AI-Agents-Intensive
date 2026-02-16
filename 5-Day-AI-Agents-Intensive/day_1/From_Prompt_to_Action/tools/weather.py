"""Weather tool implementation with OpenWeatherMap fallback logic."""

from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional, TypedDict, cast

try:
    import requests  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]

from ..tool_types import ToolErrorResponse, ToolResponse, ToolSuccessResponse

logger = logging.getLogger(__name__)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

_WEATHER_REPORTS: Dict[str, str] = {
    "new york": "The weather in New York is sunny with a temperature of 25°C (77°F).",
    "san francisco": "San Francisco is foggy with a high of 18°C (65°F).",
    "tokyo": "Tokyo is clear with a temperature of 22°C (72°F).",
}


class _WeatherEntry(TypedDict, total=False):
    description: str


class _WeatherMainInfo(TypedDict, total=False):
    temp: float


class _OpenWeatherResponse(TypedDict, total=False):
    weather: List[_WeatherEntry]
    main: _WeatherMainInfo


def get_weather(city: str) -> ToolResponse:
    """Retrieves the current weather report for a specified city."""
    city_norm = city.strip()
    city_key = city_norm.lower()

    logger.info("get_weather called city=%s", city_norm)

    if OPENWEATHER_API_KEY and requests is not None:
        params = {
            "q": city_norm,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
        }

        try:
            resp = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params=params,
                timeout=5,
            )
            resp.raise_for_status()
            data = cast(_OpenWeatherResponse, resp.json())

            weather_list: Optional[List[_WeatherEntry]] = data.get("weather")
            main_info: Optional[_WeatherMainInfo] = data.get("main")

            if not weather_list or not main_info or "temp" not in main_info:
                raise KeyError("missing 'weather' or 'main.temp' in API response")

            desc = str(weather_list[0].get("description", ""))
            temp_c = float(main_info["temp"])

            report = (
                f"The weather in {city_norm} is {desc} with a "
                f"temperature of {temp_c:.1f}°C."
            )

            logger.debug(
                "Weather fetched from API city=%s desc=%s temp=%.1f",
                city_norm,
                desc,
                temp_c,
            )
            return ToolSuccessResponse(status="success", report=report)

        except (  # pragma: no cover - defensive aggregation
            requests.RequestException,
            ValueError,
            KeyError,
        ):
            logger.exception(
                "Error while fetching weather from API for city=%s, falling back to local data",
                city_norm,
            )
    else:
        if not OPENWEATHER_API_KEY:
            logger.debug(
                "OPENWEATHER_API_KEY not set; using fallback weather data for city=%s",
                city_norm,
            )
        if requests is None:
            logger.debug(
                "requests module not available; using fallback weather data for city=%s",
                city_norm,
            )

    report = _WEATHER_REPORTS.get(city_key)
    if report:
        logger.debug("Using fallback weather report for city=%s", city_norm)
        return ToolSuccessResponse(status="success", report=report)

    available_cities = ", ".join(name.title() for name in sorted(_WEATHER_REPORTS))
    logger.warning(
        "No weather data available for city=%s available=%s",
        city_norm,
        available_cities,
    )
    return ToolErrorResponse(
        status="error",
        error_message=(
            f"Weather information for '{city_norm}' is not available. "
            f"Try: {available_cities}"
        ),
    )


__all__ = ["get_weather"]
