from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

WORKSPACE = Path("./forge_workspace")


async def execute_python(code: str, timeout: int = 30) -> str:
    """Execute Python code in the workspace directory and return the output."""
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    tmp_file = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", dir=str(WORKSPACE), delete=False) as f:
            f.write(code)
            tmp_file = f.name

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            tmp_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(WORKSPACE),
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            return f"Execution timed out after {timeout}s"

        output = ""
        if stdout:
            output += stdout.decode(errors="replace")
        if stderr:
            output += stderr.decode(errors="replace")

        output += f"\n[exit code: {process.returncode}]"
        return output.strip()

    except Exception as e:
        return f"Error executing Python code: {e}"
    finally:
        if tmp_file:
            try:
                Path(tmp_file).unlink()
            except OSError:
                pass


def register_tools(registry) -> None:
    registry.register(
        name="python_exec",
        func=execute_python,
        description="Execute Python code in the workspace directory and return the output.",
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "The Python code to execute."},
                "timeout": {"type": "integer", "description": "Timeout in seconds.", "default": 30},
            },
            "required": ["code"],
        },
    )
