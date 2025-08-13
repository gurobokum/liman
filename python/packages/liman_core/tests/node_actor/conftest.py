from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage

from liman_core.node_actor import NodeActor
from liman_core.nodes.function_node.node import FunctionNode
from liman_core.nodes.llm_node.node import LLMNode
from liman_core.nodes.tool_node.node import ToolNode
from liman_core.registry import Registry


@pytest.fixture
def llm_node(registry: Registry) -> Generator[LLMNode, None, None]:
    node_dict = {
        "kind": "LLMNode",
        "name": "test_llm_node",
        "prompts": {
            "system": {"en": "You are a helpful assistant."},
        },
    }
    with patch.object(LLMNode, "invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = AIMessage("llm_result")
        node = LLMNode.from_dict(node_dict, registry)
        node.compile()
        yield node


@pytest.fixture
def tool_node(registry: Registry) -> ToolNode:
    def test_tool_function(message: str) -> str:
        return f"Tool response: {message}"

    node_dict = {
        "kind": "ToolNode",
        "name": "test_tool_node",
        "description": {"en": "Test tool node"},
        "arguments": [
            {
                "name": "message",
                "type": "str",
                "description": {"en": "Message to process"},
            }
        ],
    }
    node = ToolNode.from_dict(node_dict, registry)
    node.set_func(test_tool_function)
    node.compile()
    return node


@pytest.fixture
def function_node(registry: Registry) -> FunctionNode:
    async def test_function() -> dict[str, Any]:
        return {"result": "test_result"}

    node_dict = {
        "kind": "FunctionNode",
        "name": "test_function_node",
        "description": {"en": "Test function node"},
    }
    node = FunctionNode.from_dict(node_dict, registry)
    node.set_func(test_function)
    node.compile()
    return node


@pytest.fixture
def llm_actor(llm_node: LLMNode) -> NodeActor[LLMNode]:
    return NodeActor(node=llm_node, llm=AsyncMock())


@pytest.fixture
def tool_actor(tool_node: ToolNode) -> NodeActor[ToolNode]:
    return NodeActor(node=tool_node)


@pytest.fixture
def function_actor(function_node: FunctionNode) -> NodeActor[FunctionNode]:
    return NodeActor(node=function_node)
