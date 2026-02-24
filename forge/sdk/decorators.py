from __future__ import annotations

import functools
from typing import Any

from forge.tools.schema import ToolSchema


def tool(_func=None, *, name: str | None = None, description: str | None = None):
    """Decorator to mark a function as a Forge tool.

    Usage:
        @tool
        async def my_tool(query: str) -> str:
            '''Search for something.'''
            return "result"

        @tool(name="custom_name", description="Does something")
        async def another_tool(x: int) -> int:
            return x * 2
    """
    def decorator(func):
        func._forge_tool = True
        func._forge_tool_name = name or func.__name__
        func._forge_tool_description = description or (func.__doc__ or "").strip()
        func._forge_tool_schema = ToolSchema.from_function(func)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        # Copy attributes to wrapper
        wrapper._forge_tool = True
        wrapper._forge_tool_name = func._forge_tool_name
        wrapper._forge_tool_description = func._forge_tool_description
        wrapper._forge_tool_schema = func._forge_tool_schema

        return wrapper

    if _func is not None:
        return decorator(_func)
    return decorator


forge_tool = tool
