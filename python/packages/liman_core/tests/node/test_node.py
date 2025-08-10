# Example YAMLs as dicts (since we don't read files directly in tests)
import pytest
from pydantic import ValidationError

from liman_core.nodes.node import Node
from liman_core.registry import Registry

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


@pytest.fixture
def registry() -> Registry:
    return Registry()


def test_llmnode_parses_style_1(registry: Registry) -> None:
    node = Node.from_dict(YAML_STYLE_1, registry)
    node.compile()
    assert node.spec.name == "BasicNode"


def test_llmnode_parses_style_2(registry: Registry) -> None:
    node = Node.from_dict(YAML_STYLE_2, registry)
    node.compile()
    assert node.spec.name == "BasicNode2"


def test_llmnode_invalid_yaml_raises(registry: Registry) -> None:
    with pytest.raises(ValidationError):
        Node.from_dict(INVALID_YAML, registry)
