"""Simple weather/time agent definition with a graceful fallback for google-adk."""

from __future__ import annotations

import datetime
import importlib
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol, Type, cast
from zoneinfo import ZoneInfo


Tool = Callable[..., Dict[str, str]]


class BaseAgent(Protocol):
    """Structural Agent interface used for typing regardless of dependency availability."""

    tools: List[Tool]

    def __init__(
        self,
        *,
        name: str,
        model: str,
        description: str,
        instruction: str,
        tools: Optional[Iterable[Tool]] = None,
        **kwargs: Any,
    ) -> None:
        ...


class _FallbackAgent:
    """Fallback Agent so this module works without google-adk."""

    def __init__(
        self,
        *,
        name: str,
        model: str,
        description: str,
        instruction: str,
        tools: Optional[Iterable[Tool]] = None,
        **kwargs: Any,
    ) -> None:
        self.name = name
        self.model = model
        self.description = description
        self.instruction = instruction
        self.tools = list(tools or [])
        self.extra_config = kwargs

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"Agent(name={self.name!r}, model={self.model!r})"


def _load_agent_class() -> Type[BaseAgent]:
    """Return the real google-adk Agent if available, otherwise fallback."""
    try:
        module = importlib.import_module("google.adk.agents")
        agent_cls = getattr(module, "Agent")
        return cast(Type[BaseAgent], agent_cls)
    except (ImportError, AttributeError):
        return _FallbackAgent


Agent: Type[BaseAgent] = _load_agent_class()

_WEATHER_REPORTS: Dict[str, str] = {
    "new york": "The weather in New York is sunny with a temperature of 25°C (77°F).",
    "san francisco": "San Francisco is foggy with a high of 18°C (65°F).",
    "tokyo": "Tokyo is clear with a temperature of 22°C (72°F).",
}

_CITY_TIMEZONES: Dict[str, str] = {
    "new york": "America/New_York",
    "san francisco": "America/Los_Angeles",
    "tokyo": "Asia/Tokyo",
}


def get_weather(city: str) -> Dict[str, str]:
    """Retrieves the current weather report for a specified city."""
    report = _WEATHER_REPORTS.get(city.lower())
    if report:
        return {"status": "success", "report": report}

    available = ", ".join(name.title() for name in sorted(_WEATHER_REPORTS))
    return {
        "status": "error",
        "error_message": f"Weather information for '{city}' is not available. Try: {available}",
    }


def get_current_time(city: str) -> Dict[str, str]:
    """Returns the current time in a specified city."""
    tz_identifier = _CITY_TIMEZONES.get(city.lower())
    if tz_identifier is None:
        available = ", ".join(name.title() for name in sorted(_CITY_TIMEZONES))
        return {
            "status": "error",
            "error_message": f"Sorry, I don't have timezone information for {city}. Try: {available}",
        }

    try:
        tz = ZoneInfo(tz_identifier)
        now = datetime.datetime.now(tz)
        report = (
            f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
        )
        return {"status": "success", "report": report}
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving time for {city}: {e}",
        }

root_agent: BaseAgent = Agent(
    name="weather_time_agent",
    model="gemini-2.0-flash",
    description=("Agent to answer questions about the time and weather in a city."),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city."
    ),
    tools=[get_weather, get_current_time],
)
