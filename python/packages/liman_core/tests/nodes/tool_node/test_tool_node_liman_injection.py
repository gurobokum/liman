import asyncio
from typing import Any

import pytest
from langchain_core.messages import ToolMessage

from liman_core.nodes.base.execution_context import ExecutionContext
from liman_core.nodes.base.liman import Liman
from liman_core.nodes.tool_node.node import ToolNode
from liman_core.nodes.tool_node.schemas import ToolCall, ToolNodeState
from liman_core.registry import Registry


def tool_with_liman(message: str, liman: Liman) -> str:
    user_id = liman.execution_context["user_id"]
    node_name = liman.get("node_state").name
    return f"User {user_id}: {message} via {node_name}"


def tool_without_liman(message: str) -> str:
    return f"Simple message: {message}"


def tool_with_mixed_params(message: str, count: int, liman: Liman) -> str:
    user_id = liman.execution_context["user_id"]
    return f"User {user_id}: {message} x{count}"


def untyped_tool_with_liman(message: str, liman: Liman) -> str:
    user_id = liman.execution_context["user_id"]
    return f"Untyped - User {user_id}: {message}"


@pytest.fixture
def liman_tool_decl() -> dict[str, Any]:
    return {
        "kind": "ToolNode",
        "name": "liman_tool",
        "description": {"en": "Tool with Liman injection"},
        "arguments": [
            {
                "name": "message",
                "type": "str",
                "description": {"en": "Message to process"},
            }
        ],
    }


@pytest.fixture
def mixed_tool_decl() -> dict[str, Any]:
    return {
        "kind": "ToolNode",
        "name": "mixed_tool",
        "description": {"en": "Tool with mixed parameters"},
        "arguments": [
            {
                "name": "message",
                "type": "str",
                "description": {"en": "Message to process"},
            },
            {
                "name": "count",
                "type": "int",
                "description": {"en": "Count parameter"},
            },
        ],
    }


def _make_execution_context(
    node: ToolNode, **kwargs: Any
) -> ExecutionContext[ToolNodeState]:
    return ExecutionContext(
        ToolNodeState(kind=node.spec.kind, name=node.spec.name), **kwargs
    )


def test_tool_with_liman_injection(
    liman_tool_decl: dict[str, Any], registry: Registry
) -> None:
    node = ToolNode.from_dict(liman_tool_decl, registry)
    node.set_func(tool_with_liman)

    tool_call = ToolCall.model_validate(
        {
            "name": "liman_tool",
            "args": {"message": "hello"},
            "id": "call_123",
            "type": "tool_call",
        }
    )

    result = asyncio.run(
        node.invoke(tool_call, _make_execution_context(node, user_id="test_user"))
    )

    assert isinstance(result, ToolMessage)
    assert result.content == "User test_user: hello via liman_tool"
    assert result.tool_call_id == "call_123"
    assert result.name == "liman_tool"


def test_tool_with_untyped_liman_parameter(
    liman_tool_decl: dict[str, Any], registry: Registry
) -> None:
    node = ToolNode.from_dict(liman_tool_decl, registry)
    node.set_func(untyped_tool_with_liman)

    tool_call = ToolCall.model_validate(
        {
            "name": "liman_tool",
            "args": {"message": "hello"},
            "id": "call_untyped",
            "type": "tool_call",
        }
    )

    result = asyncio.run(
        node.invoke(tool_call, _make_execution_context(node, user_id="test_user"))
    )

    assert isinstance(result, ToolMessage)
    assert result.content == "Untyped - User test_user: hello"


def test_tool_without_liman_still_works(
    liman_tool_decl: dict[str, Any], registry: Registry
) -> None:
    liman_tool_decl["name"] = "simple_tool"
    node = ToolNode.from_dict(liman_tool_decl, registry)
    node.set_func(tool_without_liman)

    tool_call = ToolCall.model_validate(
        {
            "name": "simple_tool",
            "args": {"message": "hello"},
            "id": "call_456",
            "type": "tool_call",
        }
    )

    result = asyncio.run(
        node.invoke(tool_call, _make_execution_context(node, user_id="test_user"))
    )

    assert isinstance(result, ToolMessage)
    assert result.content == "Simple message: hello"
    assert result.tool_call_id == "call_456"


def test_tool_with_mixed_parameters(
    mixed_tool_decl: dict[str, Any], registry: Registry
) -> None:
    node = ToolNode.from_dict(mixed_tool_decl, registry)
    node.set_func(tool_with_mixed_params)

    tool_call = ToolCall.model_validate(
        {
            "name": "mixed_tool",
            "args": {"message": "test", "count": 5},
            "id": "call_789",
            "type": "tool_call",
        }
    )

    result = asyncio.run(
        node.invoke(tool_call, _make_execution_context(node, user_id="mixed_user"))
    )

    assert isinstance(result, ToolMessage)
    assert result.content == "User mixed_user: test x5"
    assert result.tool_call_id == "call_789"


def test_missing_required_param_with_liman(
    liman_tool_decl: dict[str, Any], registry: Registry
) -> None:
    node = ToolNode.from_dict(liman_tool_decl, registry)
    node.set_func(tool_with_liman)

    tool_call = ToolCall.model_validate(
        {
            "name": "liman_tool",
            "args": {},
            "id": "call_error",
            "type": "tool_call",
        }
    )

    with pytest.raises(ValueError, match="Required parameter is missing: 'message'"):
        asyncio.run(
            node.invoke(tool_call, _make_execution_context(node, user_id="test_user"))
        )
