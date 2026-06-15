"""Plugin loader for third-party tool packages.

A Forge plugin is any importable Python module that exposes a module-level
``register_tools(registry)`` function -- the same contract the built-in tools
use (see ``forge/tools/builtin``). Inside that function a plugin calls
``registry.register(...)`` to add one or more tools.

Plugins are discovered two ways:

1. **Explicit module paths**, passed by name (e.g. from a forgefile or the
   ``Agent`` constructor)::

       loader = PluginLoader(registry)
       loader.load_module("my_package.forge_tools")

2. **Entry points** under the ``forge.plugins`` group. A distribution opts in
   via its packaging metadata::

       [project.entry-points."forge.plugins"]
       my_tools = "my_package.forge_tools"

   and Forge picks it up automatically with ``loader.load_entry_points()``.

The loader is deliberately small: it resolves the module, validates the
contract, and reports failures as :class:`PluginError` rather than letting a
broken plugin take down the host process.
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass
from importlib.metadata import entry_points
from types import ModuleType

import structlog

from forge.exceptions import ForgeError
from forge.tools.registry import ToolRegistry

logger = structlog.get_logger()

ENTRY_POINT_GROUP = "forge.plugins"
REGISTER_HOOK = "register_tools"


class PluginError(ForgeError):
    """Raised when a plugin cannot be imported or does not honor the contract."""


@dataclass(frozen=True)
class LoadedPlugin:
    """Record of a successfully loaded plugin."""

    name: str
    module: str
    tools: tuple[str, ...]


class PluginLoader:
    """Discover and register third-party tool plugins into a :class:`ToolRegistry`."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry
        self._loaded: dict[str, LoadedPlugin] = {}

    @property
    def loaded(self) -> list[LoadedPlugin]:
        """Plugins registered so far, in load order."""
        return list(self._loaded.values())

    def load_module(self, module_path: str, *, name: str | None = None) -> LoadedPlugin:
        """Import ``module_path`` and run its ``register_tools`` hook.

        Args:
            module_path: Dotted import path of the plugin module.
            name: Optional friendly name for logging; defaults to ``module_path``.

        Returns:
            A :class:`LoadedPlugin` describing the tools the plugin added.

        Raises:
            PluginError: If the module cannot be imported or lacks a callable
                ``register_tools`` function.
        """
        plugin_name = name or module_path
        if plugin_name in self._loaded:
            return self._loaded[plugin_name]

        try:
            module = importlib.import_module(module_path)
        except ImportError as exc:
            raise PluginError(
                f"Could not import plugin module '{module_path}'",
                {"module": module_path, "error": str(exc)},
            ) from exc

        return self._register_from_module(plugin_name, module)

    def load_entry_points(self) -> list[LoadedPlugin]:
        """Load every plugin advertised under the ``forge.plugins`` entry-point group.

        Failures are logged and skipped so one bad plugin cannot block the rest.

        Returns:
            The plugins that loaded successfully during this call.
        """
        loaded: list[LoadedPlugin] = []
        for ep in entry_points(group=ENTRY_POINT_GROUP):
            try:
                module = importlib.import_module(ep.value)
                loaded.append(self._register_from_module(ep.name, module))
            except (PluginError, ImportError) as exc:
                logger.warning(
                    "plugin_load_failed",
                    plugin=ep.name,
                    target=ep.value,
                    error=str(exc),
                )
        return loaded

    def _register_from_module(self, plugin_name: str, module: ModuleType) -> LoadedPlugin:
        hook = getattr(module, REGISTER_HOOK, None)
        if not callable(hook):
            raise PluginError(
                f"Plugin '{plugin_name}' has no callable '{REGISTER_HOOK}(registry)'",
                {"plugin": plugin_name, "module": module.__name__},
            )

        before = set(self._registry.list_tools())
        hook(self._registry)
        added = tuple(sorted(set(self._registry.list_tools()) - before))

        record = LoadedPlugin(name=plugin_name, module=module.__name__, tools=added)
        self._loaded[plugin_name] = record
        logger.info("plugin_loaded", plugin=plugin_name, tools=list(added))
        return record
