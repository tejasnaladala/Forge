from __future__ import annotations

import asyncio
import shlex
from pathlib import Path

from forge.config import settings

WORKSPACE = Path("./forge_workspace")

# Dangerous shell metacharacters that indicate injection attempts
_DANGEROUS_CHARS = set(";|&`$(){}><\n\\!")


def _validate_command(command: str) -> str | None:
    """Validate a shell command against the allowlist.

    Returns None if valid, or an error message string if blocked.
    """
    if not settings.sandbox_shell:
        return None

    allowed = settings.get_allowed_shell_commands()

    # Block dangerous shell metacharacters
    for char in _DANGEROUS_CHARS:
        if char in command:
            return (
                f"Blocked: shell metacharacter {char!r} is not allowed. "
                "Use simple commands without chaining or redirection."
            )

    # Extract the base command (first token)
    try:
        tokens = shlex.split(command)
    except ValueError:
        return "Blocked: malformed command string."

    if not tokens:
        return "Blocked: empty command."

    base_cmd = tokens[0].split("/")[-1]  # strip path prefix

    if base_cmd not in allowed:
        return (
            f"Blocked: command {base_cmd!r} is not in the allowlist. "
            f"Allowed commands: {', '.join(sorted(allowed))}"
        )

    return None


async def execute_shell(command: str, timeout: int = 30) -> str:
    """Execute a shell command in the workspace directory and return its output."""
    # Validate against allowlist when sandboxing is enabled
    error = _validate_command(command)
    if error:
        return error

    WORKSPACE.mkdir(parents=True, exist_ok=True)

    try:
        # Use subprocess_exec with explicit argument splitting instead of shell
        try:
            args = shlex.split(command)
        except ValueError as e:
            return f"Error parsing command: {e}"

        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(WORKSPACE),
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            return f"Command timed out after {timeout}s"

        output = ""
        if stdout:
            output += stdout.decode(errors="replace")
        if stderr:
            output += stderr.decode(errors="replace")

        output += f"\n[exit code: {process.returncode}]"
        return output.strip()

    except Exception as e:
        return f"Error executing command: {e}"


def register_tools(registry) -> None:
    registry.register(
        name="shell",
        func=execute_shell,
        description=(
            "Execute a shell command in the workspace directory. Returns stdout, stderr, and exit code. "
            "Only allowlisted commands are permitted when sandboxing is enabled."
        ),
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute."},
                "timeout": {"type": "integer", "description": "Timeout in seconds.", "default": 30},
            },
            "required": ["command"],
        },
    )
