import pytest
from pydantic import ValidationError

from liman_core.nodes.llm_node.node import LLMNode
from liman_core.registry import Registry

# Example YAMLs as dicts (since we don't read files directly in tests)
YAML_STYLE_1 = {
    "kind": "LLMNode",
    "name": "StartNode",
    "prompts": {"system": {"en": "You are a helpful assistant.", "ru": "Вы помощник."}},
}

YAML_STYLE_2 = {
    "kind": "LLMNode",
    "name": "StartNode2",
    "prompts": {
        "en": {"system": "You are a helpful assistant."},
        "ru": {"system": "Вы помощник."},
    },
}

INVALID_YAML = {
    "kind": "LLMNode",
}


def test_llmnode_parses_style_1(registry: Registry) -> None:
    node = LLMNode.from_dict(YAML_STYLE_1, registry)
    node.compile()
    assert node.spec.name == "StartNode"
    assert node.prompts.en
    assert node.prompts.en.system == "You are a helpful assistant."
    assert node.prompts.ru
    assert node.prompts.ru.system == "Вы помощник."


def test_llmnode_parses_style_2(registry: Registry) -> None:
    node = LLMNode.from_dict(YAML_STYLE_2, registry)
    node.compile()
    assert node.spec.name == "StartNode2"
    assert node.prompts.en
    assert node.prompts.en.system == "You are a helpful assistant."
    assert node.prompts.ru
    assert node.prompts.ru.system == "Вы помощник."


def test_llmnode_invalid_yaml_raises(registry: Registry) -> None:
    with pytest.raises(ValidationError):
        LLMNode.from_dict(INVALID_YAML, registry)
