"""Tests for forge.tools."""
import asyncio

import pytest

from forge.tools.registry import ToolRegistry
from forge.tools.executor import ToolExecutor
from forge.tools.schema import ToolSchema


def test_tool_registry_register_and_get():
    registry = ToolRegistry()
    async def dummy(x: str) -> str:
        return x
    registry.register("test", dummy, "A test tool", {"type": "object", "properties": {}})
    assert registry.get("test") is not None
    assert registry.get("test").name == "test"


def test_tool_registry_list_tools():
    registry = ToolRegistry()
    async def dummy(x: str) -> str:
        return x
    registry.register("a", dummy, "Tool A", {})
    registry.register("b", dummy, "Tool B", {})
    assert sorted(registry.list_tools()) == ["a", "b"]


def test_tool_registry_load_builtins():
    registry = ToolRegistry()
    registry.load_builtins()
    tools = registry.list_tools()
    assert "web_search" in tools
    assert "web_fetch" in tools
    assert "file_ops" in tools
    assert "shell" in tools
    assert "python_exec" in tools
    assert "http_request" in tools
    assert len(tools) == 6


def test_tool_registry_get_schemas():
    registry = ToolRegistry()
    registry.load_builtins()
    schemas = registry.get_schemas()
    assert len(schemas) == 6
    assert all(s["type"] == "function" for s in schemas)


def test_tool_registry_get_schemas_filtered():
    registry = ToolRegistry()
    registry.load_builtins()
    schemas = registry.get_schemas(allowed=["web_search", "shell"])
    assert len(schemas) == 2


def test_tool_registry_get_schemas_blocked():
    registry = ToolRegistry()
    registry.load_builtins()
    schemas = registry.get_schemas(blocked=["shell"])
    assert len(schemas) == 5
    assert all(s["function"]["name"] != "shell" for s in schemas)


def test_tool_schema_from_function():
    async def my_func(query: str, limit: int = 10) -> str:
        return ""
    schema = ToolSchema.from_function(my_func)
    assert schema["type"] == "object"
    assert "query" in schema["properties"]
    assert "limit" in schema["properties"]
    assert "query" in schema["required"]
    assert "limit" not in schema["required"]


@pytest.mark.asyncio
async def test_tool_executor_simple():
    registry = ToolRegistry()
    async def echo(text: str) -> str:
        return f"echo: {text}"
    registry.register("echo", echo, "Echo tool", {})
    executor = ToolExecutor(registry)
    result = await executor.execute("echo", {"text": "hello"})
    assert result == "echo: hello"


@pytest.mark.asyncio
async def test_tool_executor_not_found():
    registry = ToolRegistry()
    executor = ToolExecutor(registry)
    with pytest.raises(ValueError, match="Tool not found"):
        await executor.execute("nonexistent", {})


@pytest.mark.asyncio
async def test_tool_executor_timeout():
    registry = ToolRegistry()
    async def slow_tool() -> str:
        await asyncio.sleep(10)
        return "done"
    registry.register("slow", slow_tool, "Slow tool", {}, timeout=1)
    executor = ToolExecutor(registry)
    with pytest.raises(TimeoutError):
        await executor.execute("slow", {})
