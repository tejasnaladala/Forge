"""Third-party plugin loading for Forge.

Plugins extend the tool registry by exposing a ``register_tools(registry)``
hook. See :mod:`forge.plugins.loader` for the discovery contract.
"""
from __future__ import annotations

from forge.plugins.loader import (
    ENTRY_POINT_GROUP,
    LoadedPlugin,
    PluginError,
    PluginLoader,
)

__all__ = [
    "PluginLoader",
    "LoadedPlugin",
    "PluginError",
    "ENTRY_POINT_GROUP",
]
