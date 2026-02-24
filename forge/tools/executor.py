from __future__ import annotations

import asyncio
from typing import Any

import structlog

from forge.tools.registry import ToolRegistry

logger = structlog.get_logger()


class ToolExecutor:
    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def execute(self, tool_name: str, arguments: dict[str, Any], session_id: str = "") -> Any:
        tool = self._registry.get(tool_name)
        if tool is None:
            raise ValueError(f"Tool not found: {tool_name}")

        logger.info("tool_execute", tool=tool_name, session_id=session_id)

        try:
            result = await asyncio.wait_for(
                tool.func(**arguments),
                timeout=tool.timeout,
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"Tool '{tool_name}' timed out after {tool.timeout}s")

        return result

    def get_tool_schemas(
        self,
        allowed: list[str] | None = None,
        blocked: list[str] | None = None,
    ) -> list[dict]:
        return self._registry.get_schemas(allowed=allowed, blocked=blocked)
