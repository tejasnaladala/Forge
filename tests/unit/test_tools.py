"""Tests for forge.tools."""
import asyncio

import pytest

from forge.exceptions import ToolAuthorizationError, ToolDisabledError
from forge.tools.executor import ToolExecutor
from forge.tools.registry import ToolRegistry
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
    assert "http_request" in tools
    assert "shell" not in tools
    assert "python_exec" not in tools
    assert len(tools) == 4


def test_tool_registry_get_schemas():
    registry = ToolRegistry()
    registry.load_builtins()
    schemas = registry.get_schemas()
    assert schemas == []


def test_tool_registry_get_schemas_filtered():
    registry = ToolRegistry()
    registry.load_builtins()
    schemas = registry.get_schemas(authorized=["web_search", "file_ops"])
    assert len(schemas) == 2
    assert {schema["function"]["name"] for schema in schemas} == {"web_search", "file_ops"}


def test_tool_registry_rejects_disabled_host_execution_names():
    registry = ToolRegistry()

    async def dummy() -> str:
        return "unsafe"

    with pytest.raises(ToolDisabledError, match="OS-level isolation"):
        registry.register("shell", dummy, "Unsafe", {})

    with pytest.raises(ToolDisabledError, match="OS-level isolation"):
        registry.register("python_exec", dummy, "Unsafe", {})


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
    result = await executor.execute("echo", {"text": "hello"}, authorized={"echo"})
    assert result == "echo: hello"


@pytest.mark.asyncio
async def test_tool_executor_is_default_deny():
    registry = ToolRegistry()

    async def echo(text: str) -> str:
        return text

    registry.register("echo", echo, "Echo tool", {})
    executor = ToolExecutor(registry)

    with pytest.raises(ToolAuthorizationError, match="not authorized"):
        await executor.execute("echo", {"text": "fabricated direct call"})


@pytest.mark.asyncio
async def test_tool_executor_not_found():
    registry = ToolRegistry()
    executor = ToolExecutor(registry)
    with pytest.raises(ValueError, match="Tool not found"):
        await executor.execute("nonexistent", {}, authorized={"nonexistent"})


@pytest.mark.asyncio
async def test_tool_executor_timeout():
    registry = ToolRegistry()
    async def slow_tool() -> str:
        await asyncio.sleep(10)
        return "done"
    registry.register("slow", slow_tool, "Slow tool", {}, timeout=1)
    executor = ToolExecutor(registry)
    with pytest.raises(TimeoutError):
        await executor.execute("slow", {}, authorized={"slow"})
