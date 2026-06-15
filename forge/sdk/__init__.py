"""Forge SDK -- programmatic agent definition.

Import the high-level building blocks directly from here::

    from forge.sdk import Agent, tool

    @tool
    async def weather(city: str) -> str:
        '''Get current weather for a city.'''
        return f"Weather in {city}: 72F and sunny"

    agent = Agent("weather-bot", model="claude-sonnet-4-20250514", tools=[weather])
"""
from __future__ import annotations

from forge.sdk.agent import Agent
from forge.sdk.decorators import forge_tool, tool

__all__ = ["Agent", "tool", "forge_tool"]
