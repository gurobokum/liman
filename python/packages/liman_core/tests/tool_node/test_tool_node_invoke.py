from typing import Any

import pytest
from langchain_core.messages import ToolMessage

from liman_core.errors import LimanError
from liman_core.nodes.base.schemas import NodeOutput
from liman_core.nodes.tool_node.node import ToolNode
from liman_core.registry import Registry


def sync_test_func(location: str, temperature: int = 20) -> str:
    """
    Test sync function for tool node testing.
    """
    return f"Weather in {location}: {temperature}°C"


def sync_failing_func(location: str) -> str:
    """
    Test sync function that always raises an exception.
    """
    raise ValueError(f"Cannot get weather for {location}")


def sync_func_with_optional(name: str, greeting: str = "Hello") -> str:
    """
    Test sync function with optional parameter.
    """
    return f"{greeting}, {name}!"


@pytest.fixture
def tool_node_decl() -> dict[str, Any]:
    return {
        "kind": "ToolNode",
        "name": "weather_tool",
        "description": {"en": "Get weather information"},
        "arguments": [
            {
                "name": "location",
                "type": "str",
                "description": {"en": "City name"},
            },
            {
                "name": "temperature",
                "type": "int",
                "description": {"en": "Temperature"},
                "optional": True,
            },
        ],
    }


@pytest.fixture
def greeting_tool_decl() -> dict[str, Any]:
    return {
        "kind": "ToolNode",
        "name": "greeting_tool",
        "description": {"en": "Generate greeting"},
    }


@pytest.fixture
def registry() -> Registry:
    return Registry()


def test_invoke_with_valid_tool_call(
    tool_node_decl: dict[str, Any], registry: Registry
) -> None:
    node = ToolNode.from_dict(tool_node_decl, registry)
    node.set_func(sync_test_func)

    tool_call = {
        "name": "weather_tool",
        "args": {"location": "Moscow", "temperature": 25},
        "id": "call_123",
        "type": "tool_call",
    }

    result = node.invoke(tool_call)

    assert isinstance(result, NodeOutput)
    assert isinstance(result.response, ToolMessage)
    assert result.response.content == "Weather in Moscow: 25°C"
    assert result.response.tool_call_id == "call_123"
    assert result.response.name == "weather_tool"


def test_invoke_with_missing_optional_param(
    tool_node_decl: dict[str, Any], registry: Registry
) -> None:
    node = ToolNode.from_dict(tool_node_decl, registry)
    node.set_func(sync_test_func)

    tool_call = {
        "name": "weather_tool",
        "args": {"location": "Berlin"},
        "id": "call_456",
        "type": "tool_call",
    }

    result = node.invoke(tool_call)

    assert isinstance(result, NodeOutput)
    assert isinstance(result.response, ToolMessage)
    assert result.response.content == "Weather in Berlin: 20°C"
    assert result.response.tool_call_id == "call_456"
    assert result.response.name == "weather_tool"


def test_invoke_with_extra_params_filtered(
    tool_node_decl: dict[str, Any], registry: Registry
) -> None:
    node = ToolNode.from_dict(tool_node_decl, registry)
    node.set_func(sync_test_func)

    tool_call = {
        "name": "weather_tool",
        "args": {
            "location": "Paris",
            "temperature": 18,
            "extra_param": "should_be_ignored",
            "another_extra": 42,
        },
        "id": "call_789",
        "type": "tool_call",
    }

    result = node.invoke(tool_call)

    assert isinstance(result, NodeOutput)
    assert isinstance(result.response, ToolMessage)
    assert result.response.content == "Weather in Paris: 18°C"
    assert result.response.tool_call_id == "call_789"
    assert result.response.name == "weather_tool"


def test_invoke_with_missing_required_param(
    tool_node_decl: dict[str, Any], registry: Registry
) -> None:
    node = ToolNode.from_dict(tool_node_decl, registry)
    node.set_func(sync_test_func)

    tool_call = {
        "name": "weather_tool",
        "args": {"temperature": 30},
        "id": "call_error",
        "type": "tool_call",
    }

    with pytest.raises(ValueError, match="Required parameter is missing: 'location'"):
        node.invoke(tool_call)


def test_invoke_with_function_exception(
    tool_node_decl: dict[str, Any], registry: Registry
) -> None:
    node = ToolNode.from_dict(tool_node_decl, registry)
    node.set_func(sync_failing_func)

    tool_call = {
        "name": "weather_tool",
        "args": {"location": "UnknownCity"},
        "id": "call_fail",
        "type": "tool_call",
    }

    result = node.invoke(tool_call)

    assert isinstance(result, NodeOutput)
    assert isinstance(result.response, ToolMessage)
    assert "Cannot get weather for UnknownCity" in result.response.content
    assert result.response.tool_call_id == "call_fail"
    assert result.response.name == "weather_tool"


def test_invoke_missing_args_field(
    tool_node_decl: dict[str, Any], registry: Registry
) -> None:
    node = ToolNode.from_dict(tool_node_decl, registry)
    node.set_func(sync_test_func)

    tool_call = {
        "name": "weather_tool",
        "id": "call_no_args",
        "type": "tool_call",
    }

    with pytest.raises(LimanError, match="must contain 'args' field"):
        node.invoke(tool_call)


def test_invoke_with_optional_param_function(
    greeting_tool_decl: dict[str, Any], registry: Registry
) -> None:
    node = ToolNode.from_dict(greeting_tool_decl, registry)
    node.set_func(sync_func_with_optional)

    # Test with optional parameter provided
    tool_call = {
        "name": "greeting_tool",
        "args": {"name": "Alice", "greeting": "Hi"},
        "id": "call_greeting1",
        "type": "tool_call",
    }

    result = node.invoke(tool_call)
    assert result.response.content == "Hi, Alice!"


def test_invoke_with_optional_param_function_no_arg(
    greeting_tool_decl: dict[str, Any], registry: Registry
) -> None:
    node = ToolNode.from_dict(greeting_tool_decl, registry)
    node.set_func(sync_func_with_optional)

    tool_call = {
        "name": "greeting_tool",
        "args": {"name": "Bob"},
        "id": "call_greeting2",
        "type": "tool_call",
    }

    result = node.invoke(tool_call)
    assert result.response.content == "Hello, Bob!"
