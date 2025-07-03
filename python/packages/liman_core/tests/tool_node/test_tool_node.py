from typing import Any

from liman_core.tool_node.node import ToolNode


def test_tool_node_minimal(simple_decl: dict[str, Any]) -> None:
    node = ToolNode.from_yaml(simple_decl)
    assert node.name == "test_tool"
    assert node.kind == "ToolNode"
    assert node.spec.description["en"] == "Test tool description."


def test_tool_node_get_tool_description_en(decl_with_triggers: dict[str, Any]) -> None:
    node = ToolNode.from_yaml(decl_with_triggers)

    desc = node.get_tool_description("en")
    assert "Weather tool." in desc
    assert "What's the weather?" in desc
    assert "Weather in Moscow" in desc
    assert "Forecast" in desc
    assert desc.startswith("weather - Weather tool.")


def test_tool_node_get_tool_description_ru(decl_with_triggers: dict[str, Any]) -> None:
    decl_with_triggers["name"] = "weather2"
    node = ToolNode.from_yaml(decl_with_triggers)

    desc = node.get_tool_description("ru")
    assert "Погода." in desc
    assert "Какая погода?" in desc
    assert "Погода в Москве" in desc
    assert "Forecast" in desc
    assert desc.startswith("weather2 - Погода.")


def test_tool_node_default_template_if_missing(simple_decl: dict[str, Any]) -> None:
    simple_decl["name"] = "test_tool2"
    node = ToolNode.from_yaml(simple_decl)

    desc = node.get_tool_description("en")
    assert "Test tool description." in desc
    assert desc == "test_tool2 - Test tool description."
