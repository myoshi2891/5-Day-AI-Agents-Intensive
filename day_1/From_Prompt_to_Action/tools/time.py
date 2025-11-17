"""Time tool implementation built on zoneinfo."""

from __future__ import annotations

import datetime
import logging
from typing import Dict
from zoneinfo import ZoneInfo

from ..tool_types import ToolErrorResponse, ToolResponse, ToolSuccessResponse

logger = logging.getLogger(__name__)

_CITY_TIMEZONES: Dict[str, str] = {
    "new york": "America/New_York",
    "san francisco": "America/Los_Angeles",
    "tokyo": "Asia/Tokyo",
}


def get_current_time(city: str) -> ToolResponse:
    """Returns the current time in a specified city."""
    city_norm = city.strip()
    city_key = city_norm.lower()

    logger.info("get_current_time called city=%s", city_norm)

    tz_identifier = _CITY_TIMEZONES.get(city_key)
    if tz_identifier is None:
        available = ", ".join(name.title() for name in sorted(_CITY_TIMEZONES))
        logger.warning(
            "Timezone not found for city=%s available=%s",
            city_norm,
            available,
        )
        return ToolErrorResponse(
            status="error",
            error_message=(
                f"Sorry, I don't have timezone information for {city_norm}. "
                f"Try: {available}"
            ),
        )

    try:
        tz = ZoneInfo(tz_identifier)
        now = datetime.datetime.now(tz)
        report = (
            f'The current time in {city_norm} is '
            f'{now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
        )

        logger.debug(
            "Time resolved city=%s tz=%s report=%s",
            city_norm,
            tz_identifier,
            report,
        )
        return ToolSuccessResponse(status="success", report=report)

    except Exception:  # pragma: no cover
        logger.exception(
            "Error retrieving time for city=%s tz=%s", city_norm, tz_identifier
        )
        return ToolErrorResponse(
            status="error",
            error_message=f"Error retrieving time for {city_norm}.",
        )


__all__ = ["get_current_time"]
