# Example YAMLs as dicts (since we don't read files directly in tests)
import pytest
from pydantic import ValidationError

from liman_core.node import Node

YAML_STYLE_1 = {
    "kind": "Node",
    "name": "BasicNode",
    "func": "basic_function",
    "description": {
        "en": "This is a basic node.",
        "ru": "Это базовый шаг.",
    },
}

YAML_STYLE_2 = {
    "kind": "Node",
    "name": "BasicNode2",
    "func": "basic_function2",
    "description": {
        "en": "This is another basic node.",
        "ru": "Это другой базовый шаг.",
    },
}

INVALID_YAML = {
    "kind": "Node",
}


def test_llmnode_parses_style_1() -> None:
    node = Node.from_dict(YAML_STYLE_1)
    node.compile()
    assert node.spec.name == "BasicNode"


def test_llmnode_parses_style_2() -> None:
    node = Node.from_dict(YAML_STYLE_2)
    node.compile()
    assert node.spec.name == "BasicNode2"


def test_llmnode_invalid_yaml_raises() -> None:
    with pytest.raises(ValidationError):
        Node.from_dict(INVALID_YAML)
