from typing import Any

import pytest

from liman_core.nodes.tool_node.node import ToolNode
from liman_core.registry import Registry


@pytest.fixture
def registry() -> Registry:
    return Registry()


def test_tool_node_minimal(simple_decl: dict[str, Any], registry: Registry) -> None:
    node = ToolNode.from_dict(simple_decl, registry)
    assert node.name == "test_tool"
    assert node.spec.kind == "ToolNode"
    assert node.spec.description["en"] == "Test tool description."


def test_tool_node_get_tool_description_en(
    decl_with_triggers: dict[str, Any], registry: Registry
) -> None:
    node = ToolNode.from_dict(decl_with_triggers, registry)

    desc = node.get_tool_description("en")
    assert "Weather tool." in desc
    assert "What's the weather?" in desc
    assert "Weather in Moscow" in desc
    assert "Forecast" in desc
    assert desc.startswith("weather - Weather tool.")


def test_tool_node_get_tool_description_ru(
    decl_with_triggers: dict[str, Any], registry: Registry
) -> None:
    decl_with_triggers["name"] = "weather2"
    node = ToolNode.from_dict(decl_with_triggers, registry)

    desc = node.get_tool_description("ru")
    assert "Погода." in desc
    assert "Какая погода?" in desc
    assert "Погода в Москве" in desc
    assert "Forecast" in desc
    assert desc.startswith("weather2 - Погода.")


def test_tool_node_default_template_if_missing(
    simple_decl: dict[str, Any], registry: Registry
) -> None:
    simple_decl["name"] = "test_tool2"
    node = ToolNode.from_dict(simple_decl, registry)

    desc = node.get_tool_description("en")
    assert "Test tool description." in desc
    assert desc == "test_tool2 - Test tool description."
