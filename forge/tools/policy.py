from __future__ import annotations

from collections.abc import Iterable

DISABLED_HOST_EXECUTION_TOOLS = frozenset({"python_exec", "shell"})


def normalize_authorized_tools(tool_names: Iterable[str] | None) -> frozenset[str]:
    """Return an immutable allowlist; missing policy always means no tools."""
    return frozenset(tool_names or ())


def host_execution_disabled_message(tool_name: str) -> str:
    return (
        f"Tool {tool_name!r} is disabled. Forge does not currently provide the OS-level "
        "isolation required to execute model-controlled Python or shell commands safely."
    )
