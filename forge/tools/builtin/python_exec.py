from __future__ import annotations

from forge.exceptions import ToolDisabledError
from forge.tools.policy import host_execution_disabled_message


async def execute_python(code: str, timeout: int = 30) -> str:
    """Reject host Python execution until Forge has real OS isolation."""
    del code, timeout
    raise ToolDisabledError(host_execution_disabled_message("python_exec"))


def register_tools(registry) -> None:
    """Prevent direct or plugin-style re-registration of host Python execution."""
    del registry
    raise ToolDisabledError(host_execution_disabled_message("python_exec"))
