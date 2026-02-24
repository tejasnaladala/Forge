"""Tests for forge.core.parser."""
import tempfile
from pathlib import Path

import pytest

from forge.core.parser import ForgefileParser
from forge.core.types import ModelProvider


@pytest.fixture
def parser():
    return ForgefileParser()


def test_parse_model_shorthand_gpt(parser):
    config = ForgefileParser._parse_model_shorthand("gpt-4o")
    assert config.provider == ModelProvider.OPENAI
    assert config.model == "gpt-4o"


def test_parse_model_shorthand_claude(parser):
    config = ForgefileParser._parse_model_shorthand("claude-sonnet-4-20250514")
    assert config.provider == ModelProvider.ANTHROPIC


def test_parse_model_shorthand_ollama_prefix(parser):
    config = ForgefileParser._parse_model_shorthand("ollama/llama3.1:8b")
    assert config.provider == ModelProvider.OLLAMA
    assert config.model == "llama3.1:8b"


def test_parse_model_shorthand_ollama_inferred(parser):
    config = ForgefileParser._parse_model_shorthand("llama3.2:3b")
    assert config.provider == ModelProvider.OLLAMA


def test_parse_model_shorthand_deepseek(parser):
    config = ForgefileParser._parse_model_shorthand("deepseek-chat")
    assert config.provider == ModelProvider.DEEPSEEK


def test_parse_agent_simple(parser):
    raw = {"name": "test", "model": "gpt-4o", "system_prompt": "Hello"}
    config = parser._parse_agent(raw)
    assert config.name == "test"
    assert config.model.provider == ModelProvider.OPENAI
    assert config.system_prompt == "Hello"


def test_parse_agent_with_tools(parser):
    raw = {"name": "test", "model": "gpt-4o", "tools": ["web_search", "file_ops"]}
    config = parser._parse_agent(raw)
    assert len(config.tools) == 2
    assert config.tools[0].name == "web_search"


def test_parse_dict_single_agent(parser):
    raw = {"agent": {"name": "solo", "model": "gpt-4o"}}
    result = parser.parse_dict(raw)
    assert "solo" in result["agents"]


def test_parse_dict_multiple_agents(parser):
    raw = {"agents": [{"name": "a1", "model": "gpt-4o"}, {"name": "a2", "model": "ollama/llama3.2:3b"}]}
    result = parser.parse_dict(raw)
    assert "a1" in result["agents"]
    assert "a2" in result["agents"]


def test_parse_file(parser, tmp_path):
    yaml_content = "agent:\\n  name: test\\n  model: gpt-4o\\n  system_prompt: Hello\\n"
    f = tmp_path / "forgefile.yaml"
    f.write_text(yaml_content.replace("\\n", "\n"))
    result = parser.parse_file(f)
    assert "test" in result["agents"]
