from __future__ import annotations

from forge.exceptions import ToolDisabledError
from forge.tools.policy import host_execution_disabled_message


async def execute_shell(command: str, timeout: int = 30) -> str:
    """Reject host shell execution until Forge has real OS isolation."""
    del command, timeout
    raise ToolDisabledError(host_execution_disabled_message("shell"))


def register_tools(registry) -> None:
    """Prevent direct or plugin-style re-registration of host shell execution."""
    del registry
    raise ToolDisabledError(host_execution_disabled_message("shell"))
