from __future__ import annotations

import asyncio
from pathlib import Path

WORKSPACE = Path("./forge_workspace")


async def execute_shell(command: str, timeout: int = 30) -> str:
    """Execute a shell command in the workspace directory."""
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    try:
        process = await asyncio.create_subprocess_shell(
            command,
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
        description="Execute a shell command in the workspace directory. Returns stdout, stderr, and exit code.",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30},
            },
            "required": ["command"],
        },
    )
