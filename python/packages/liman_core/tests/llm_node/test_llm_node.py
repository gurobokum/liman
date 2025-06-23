import pytest
from pydantic import ValidationError

from liman_core.llm_node import LLMNode

# Example YAMLs as dicts (since we don't read files directly in tests)
YAML_STYLE_1 = {
    "kind": "LLMNode",
    "name": "StartNode",
    "prompts": {"system": {"en": "You are a helpful assistant.", "ru": "Вы помощник."}},
    "tools": ["WeatherTool", "EmailTool"],
}

YAML_STYLE_2 = {
    "kind": "LLMNode",
    "name": "StartNode",
    "prompts": {
        "en": {"system": "You are a helpful assistant."},
        "ru": {"system": "Вы помощник."},
    },
    "tools": ["WeatherTool", "EmailTool"],
}

INVALID_YAML = {
    "kind": "LLMNode",
    # Missing 'name' and 'prompts'
    "tools": ["WeatherTool"],
}

INVALID_YAML_IMPRPOER_KIND = {
    "kind": "InvalidNodeKind",
    "name": "StartNode",
    "prompts": {"system": {"en": "You are a helpful assistant."}},
    "tools": ["WeatherTool", "EmailTool"],
}


def test_llmnode_parses_style_1() -> None:
    node = LLMNode(name="StartNode", declaration=YAML_STYLE_1)
    node.compile()
    assert node.spec.name == "StartNode"
    assert node.prompts.en
    assert node.prompts.en.system == "You are a helpful assistant."
    assert node.prompts.ru
    assert node.prompts.ru.system == "Вы помощник."


def test_llmnode_parses_style_2() -> None:
    node = LLMNode(name="StartNode2", declaration=YAML_STYLE_2)
    node.compile()
    assert node.spec.name == "StartNode"
    assert node.prompts.en
    assert node.prompts.en.system == "You are a helpful assistant."
    assert node.prompts.ru
    assert node.prompts.ru.system == "Вы помощник."


def test_llmnode_invalid_yaml_raises() -> None:
    with pytest.raises(ValidationError):
        LLMNode(name="InvalidLLMNode", declaration=INVALID_YAML)
