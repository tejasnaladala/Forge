from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from forge.core.parser import ForgefileParser
from forge.exceptions import ToolDisabledError
from forge.tools.builtin.python_exec import execute_python
from forge.tools.builtin.shell import execute_shell
from forge.tools.executor import ToolExecutor
from forge.tools.registry import ToolRegistry

PYTHON_ESCAPE_ATTEMPTS = [
    "from pathlib import Path; print(Path('../README.md').read_text())",
    "import os; print(os.environ)",
    "import urllib.request; urllib.request.urlopen('https://example.com')",
    "import subprocess; subprocess.run(['whoami'])",
]

SHELL_ESCAPE_ATTEMPTS = [
    "cat ../README.md",
    "env",
    "curl https://example.com",
    "python -c \"import subprocess; subprocess.run(['whoami'])\"",
]

TEMPLATE_ESCAPE_ATTEMPTS = [
    "{{ cycler.__init__.__globals__.os.environ['FORGE_TEMPLATE_SECRET'] }}",
    "{{ lipsum.__globals__['os'].popen('cat ../README.md').read() }}",
    "{{ ''.__class__.__mro__[1].__subclasses__() }}",
    "{{ __import__('urllib.request').request.urlopen('https://example.com').read() }}",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", PYTHON_ESCAPE_ATTEMPTS)
async def test_python_execution_rejects_path_env_network_and_subprocess(payload):
    process_spy = AsyncMock(side_effect=AssertionError("host process creation attempted"))
    with patch.object(asyncio, "create_subprocess_exec", process_spy):
        with pytest.raises(ToolDisabledError, match="OS-level isolation"):
            await execute_python(payload)
    process_spy.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("command", SHELL_ESCAPE_ATTEMPTS)
async def test_shell_execution_rejects_path_env_network_and_subprocess(command):
    process_spy = AsyncMock(side_effect=AssertionError("host process creation attempted"))
    with patch.object(asyncio, "create_subprocess_exec", process_spy):
        with pytest.raises(ToolDisabledError, match="OS-level isolation"):
            await execute_shell(command)
    process_spy.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("tool_name", ["shell", "python_exec"])
async def test_executor_rejects_fabricated_host_execution_calls(tool_name):
    executor = ToolExecutor(ToolRegistry())
    with pytest.raises(ToolDisabledError, match="OS-level isolation"):
        await executor.execute(tool_name, {}, authorized={tool_name})


@pytest.mark.parametrize("payload", TEMPLATE_ESCAPE_ATTEMPTS)
def test_system_prompt_templates_are_never_evaluated(payload, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FORGE_TEMPLATE_SECRET", "must-not-be-rendered")
    parser = ForgefileParser()

    config = parser._parse_agent({"name": "literal-prompt", "system_prompt": payload})

    assert config.system_prompt == payload
    assert "must-not-be-rendered" not in config.system_prompt
    assert list(tmp_path.iterdir()) == []
