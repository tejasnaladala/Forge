from __future__ import annotations

import asyncio
from typing import Any

import structlog

from forge.exceptions import ToolAuthorizationError, ToolDisabledError
from forge.tools.policy import (
    DISABLED_HOST_EXECUTION_TOOLS,
    host_execution_disabled_message,
    normalize_authorized_tools,
)
from forge.tools.registry import ToolRegistry

logger = structlog.get_logger()


class ToolExecutor:
    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        session_id: str = "",
        *,
        authorized: list[str] | set[str] | frozenset[str] | None = None,
    ) -> Any:
        if tool_name in DISABLED_HOST_EXECUTION_TOOLS:
            raise ToolDisabledError(host_execution_disabled_message(tool_name))

        authorized_names = normalize_authorized_tools(authorized)
        if tool_name not in authorized_names:
            raise ToolAuthorizationError(f"Tool {tool_name!r} is not authorized for this agent")

        tool = self._registry.get(tool_name)
        if tool is None:
            raise ValueError(f"Tool not found: {tool_name}")

        # Validate argument types -- only allow str, int, float, bool, list, dict, None
        sanitized = {}
        for key, value in arguments.items():
            if not isinstance(key, str):
                raise ValueError(f"Tool argument key must be a string, got {type(key).__name__}")
            if value is not None and not isinstance(value, (str, int, float, bool, list, dict)):
                raise ValueError(f"Tool argument '{key}' has unsupported type {type(value).__name__}")
            sanitized[key] = value

        logger.info("tool_execute", tool=tool_name, session_id=session_id)

        try:
            result = await asyncio.wait_for(
                tool.func(**sanitized),
                timeout=tool.timeout,
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"Tool '{tool_name}' timed out after {tool.timeout}s")

        return result

    def get_tool_schemas(
        self,
        authorized: list[str] | set[str] | frozenset[str] | None = None,
    ) -> list[dict]:
        return self._registry.get_schemas(authorized=authorized)
