from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path

WORKSPACE = Path("./forge_workspace")


def _safe_resolve(path: str) -> tuple[Path, str | None]:
    """Resolve a path and verify it stays within WORKSPACE.

    Returns (resolved_path, error_message). error_message is None on success.
    """
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    workspace_resolved = WORKSPACE.resolve()

    # Reject absolute paths outright
    if os.path.isabs(path):
        return Path(), "Error: absolute paths are not allowed. Use paths relative to the workspace."

    target = (WORKSPACE / path).resolve()

    # Ensure the resolved target is within the workspace
    try:
        target.relative_to(workspace_resolved)
    except ValueError:
        return Path(), f"Error: path {path!r} escapes the workspace directory. Path traversal is not allowed."

    return target, None


def _sync_file_op(operation: str, path: str, content: str) -> str:
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    target, error = _safe_resolve(path)
    if error:
        return error

    if operation == "read":
        if not target.is_file():
            return f"Error: {path} is not a file or does not exist"
        return target.read_text(encoding="utf-8")

    elif operation == "write":
        # Re-validate parent directory stays in workspace
        parent = target.parent
        workspace_resolved = WORKSPACE.resolve()
        try:
            parent.relative_to(workspace_resolved)
        except ValueError:
            return "Error: write target parent escapes the workspace directory."
        parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Written {len(content)} bytes to {path}"

    elif operation == "list":
        if not target.exists():
            return f"Error: {path} does not exist"
        files = []
        for root, dirs, filenames in os.walk(target):
            for fname in filenames:
                rel = os.path.relpath(os.path.join(root, fname), WORKSPACE)
                files.append(rel)
        return "\n".join(sorted(files)) if files else "(empty)"

    elif operation == "delete":
        if not target.exists():
            return f"Error: {path} does not exist"
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        return f"Deleted {path}"

    elif operation == "exists":
        return "true" if target.exists() else "false"

    else:
        return f"Error: Unknown operation '{operation}'. Use: read, write, list, delete, exists"


async def file_operations(operation: str, path: str = ".", content: str = "") -> str:
    """Perform file operations in the workspace directory."""
    return await asyncio.to_thread(_sync_file_op, operation, path, content)


def register_tools(registry) -> None:
    registry.register(
        name="file_ops",
        func=file_operations,
        description="Perform file operations (read, write, list, delete, exists) in the workspace directory.",
        parameters={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Operation to perform: read, write, list, delete, exists.",
                    "enum": ["read", "write", "list", "delete", "exists"],
                },
                "path": {"type": "string", "description": "File or directory path relative to the workspace.", "default": "."},
                "content": {"type": "string", "description": "Content to write (for the write operation).", "default": ""},
            },
            "required": ["operation"],
        },
    )
