from __future__ import annotations

import asyncio
import re
import sys
import tempfile
from pathlib import Path

from forge.config import settings

WORKSPACE = Path("./forge_workspace")

# Modules that should never be imported in sandboxed mode
_BLOCKED_IMPORTS = {
    "subprocess", "shutil", "ctypes", "importlib", "code", "codeop",
    "compileall", "py_compile", "zipimport", "pkgutil",
}

# Patterns that indicate dangerous operations
_DANGEROUS_PATTERNS = [
    re.compile(r"\bos\.system\b"),
    re.compile(r"\bos\.popen\b"),
    re.compile(r"\bos\.exec\w*\b"),
    re.compile(r"\bos\.spawn\w*\b"),
    re.compile(r"\bos\.remove\b"),
    re.compile(r"\bos\.unlink\b"),
    re.compile(r"\bos\.rmdir\b"),
    re.compile(r"\bos\.rename\b"),
    re.compile(r"\bos\.environ\b"),
    re.compile(r"\b__import__\b"),
    re.compile(r"\beval\s*\("),
    re.compile(r"\bexec\s*\("),
    re.compile(r"\bcompile\s*\("),
    re.compile(r"\bopen\s*\(.+,\s*['\"]w"),
    re.compile(r"\bsocket\b"),
    re.compile(r"\breversed?\s*shell", re.IGNORECASE),
]


def _validate_code(code: str) -> str | None:
    """Validate Python code for dangerous patterns when sandbox is enabled.

    Returns None if safe, or an error message string if blocked.
    """
    if not settings.sandbox_python:
        return None

    # Check for blocked imports
    import_pattern = re.compile(r"(?:^|\n)\s*(?:import|from)\s+(\w+)")
    for match in import_pattern.finditer(code):
        module = match.group(1)
        if module in _BLOCKED_IMPORTS:
            return f"Blocked: import of {module!r} is not allowed in sandboxed mode."

    # Check for dangerous patterns
    for pattern in _DANGEROUS_PATTERNS:
        if pattern.search(code):
            return f"Blocked: dangerous pattern detected ({pattern.pattern}). This operation is not allowed in sandboxed mode."

    return None


async def execute_python(code: str, timeout: int = 30) -> str:
    """Execute Python code in the workspace directory and return the output."""
    # Validate code against blocklist when sandboxing is enabled
    error = _validate_code(code)
    if error:
        return error

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
        description=(
            "Execute Python code in the workspace directory and return the output. "
            "Dangerous operations (os.system, subprocess, eval, etc.) are blocked when sandboxing is enabled."
        ),
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "The Python code to execute."},
                "timeout": {"type": "integer", "description": "Timeout in seconds.", "default": 30},
            },
            "required": ["code"],
        },
    )
