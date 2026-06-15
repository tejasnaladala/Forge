"""Tests for forge.plugins.loader."""
import sys
import types

import pytest

from forge.plugins.loader import LoadedPlugin, PluginError, PluginLoader
from forge.tools.registry import ToolRegistry


def _make_plugin_module(name: str, tool_names: list[str]) -> types.ModuleType:
    """Build an in-memory plugin module exposing register_tools()."""
    module = types.ModuleType(name)

    def register_tools(registry: ToolRegistry) -> None:
        async def _noop(x: str = "") -> str:
            return x

        for tool_name in tool_names:
            registry.register(tool_name, _noop, f"{tool_name} tool", {})

    module.register_tools = register_tools
    return module


@pytest.fixture
def injected_module(request):
    """Register a fake plugin module in sys.modules and clean it up after."""
    created: list[str] = []

    def _inject(name: str, tool_names: list[str]) -> str:
        sys.modules[name] = _make_plugin_module(name, tool_names)
        created.append(name)
        return name

    yield _inject

    for name in created:
        sys.modules.pop(name, None)


def test_load_module_registers_tools(injected_module):
    registry = ToolRegistry()
    name = injected_module("fake_forge_plugin_a", ["plugin_tool_a", "plugin_tool_b"])

    loader = PluginLoader(registry)
    record = loader.load_module(name)

    assert isinstance(record, LoadedPlugin)
    assert record.tools == ("plugin_tool_a", "plugin_tool_b")
    assert "plugin_tool_a" in registry.list_tools()
    assert "plugin_tool_b" in registry.list_tools()


def test_load_module_is_idempotent(injected_module):
    registry = ToolRegistry()
    name = injected_module("fake_forge_plugin_b", ["only_tool"])

    loader = PluginLoader(registry)
    first = loader.load_module(name)
    second = loader.load_module(name)

    assert first is second
    assert len(loader.loaded) == 1


def test_load_module_missing_module_raises():
    registry = ToolRegistry()
    loader = PluginLoader(registry)

    with pytest.raises(PluginError) as exc:
        loader.load_module("forge_plugin_that_does_not_exist_xyz")
    assert "Could not import" in str(exc.value)


def test_load_module_without_hook_raises(injected_module):
    registry = ToolRegistry()
    name = "fake_forge_plugin_no_hook"
    sys.modules[name] = types.ModuleType(name)  # no register_tools

    loader = PluginLoader(registry)
    try:
        with pytest.raises(PluginError) as exc:
            loader.load_module(name)
        assert "register_tools" in str(exc.value)
    finally:
        sys.modules.pop(name, None)


def test_registry_load_plugins_returns_added_tool_names(injected_module):
    registry = ToolRegistry()
    name = injected_module("fake_forge_plugin_c", ["x_tool", "y_tool"])

    added = registry.load_plugins(modules=[name], entry_points=False)

    assert sorted(added) == ["x_tool", "y_tool"]
