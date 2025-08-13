from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from liman_core.node_actor import NodeActor, NodeActorError, NodeActorStatus
from liman_core.node_actor.schemas import Result
from liman_core.nodes.function_node.node import FunctionNode
from liman_core.nodes.llm_node.node import LLMNode
from liman_core.nodes.tool_node.node import ToolNode
from liman_core.nodes.tool_node.schemas import ToolCall
from liman_core.registry import Registry


def test_actor_create_method(function_node: FunctionNode) -> None:
    actor = NodeActor.create(node=function_node)

    assert isinstance(actor, NodeActor)
    assert actor.node is function_node
    assert actor.status == NodeActorStatus.READY


def test_actor_initialization_on_create(llm_actor: NodeActor[LLMNode]) -> None:
    assert llm_actor.status == NodeActorStatus.READY


def test_actor_compiles_uncompiled_node(registry: Registry) -> None:
    async def test_func() -> dict[str, Any]:
        return {"result": "compiled_result"}

    node_dict = {
        "kind": "FunctionNode",
        "name": "uncompiled_node",
    }
    node = FunctionNode.from_dict(node_dict, registry)
    node.set_func(test_func)
    # Don't compile yet
    assert not node._compiled

    actor = NodeActor(node=node)

    assert actor.status == NodeActorStatus.READY
    assert node._compiled


async def test_actor_execute_success(function_actor: NodeActor[FunctionNode]) -> None:
    inputs = "test"
    execution_id = uuid4()

    result = await function_actor.execute(inputs, execution_id)

    assert isinstance(result, Result)
    assert result.output == {"result": "test_result"}
    assert function_actor.status == NodeActorStatus.COMPLETED


async def test_actor_execute_from_idle_status_raises(
    function_node: FunctionNode,
) -> None:
    import asyncio

    actor = NodeActor.__new__(NodeActor)
    actor.node = function_node
    actor.status = NodeActorStatus.IDLE
    actor.id = uuid4()
    actor._execution_lock = asyncio.Lock()
    inputs = "test"
    execution_id = uuid4()

    with pytest.raises(NodeActorError) as exc_info:
        await actor.execute(inputs, execution_id)

    assert "Cannot execute actor in status" in str(exc_info.value)


async def test_actor_execute_after_shutdown_raises(
    llm_actor: NodeActor[LLMNode],
) -> None:
    llm_actor.status = NodeActorStatus.SHUTDOWN
    inputs = "test"
    execution_id = uuid4()

    with pytest.raises(NodeActorError) as exc_info:
        await llm_actor.execute(inputs, execution_id)

    assert "Cannot execute actor in status shutdown" in str(exc_info.value)


async def test_actor_execute_with_context(llm_actor: NodeActor[LLMNode]) -> None:
    inputs = "test"
    context = {"custom_key": "custom_value"}
    execution_id = uuid4()

    await llm_actor.execute(inputs, execution_id, context=context)

    call_kwargs = llm_actor.node.invoke.call_args[1]  # type: ignore[attr-defined]
    assert call_kwargs["custom_key"] == "custom_value"
    assert call_kwargs["actor_id"] == llm_actor.id
    assert call_kwargs["execution_id"] == execution_id


async def test_actor_execute_llm_node_success(llm_actor: NodeActor[LLMNode]) -> None:
    inputs = "test"
    execution_id = uuid4()

    result = await llm_actor.execute(inputs, execution_id)

    assert isinstance(result, Result)
    assert result.output.content == "llm_result"
    cast(AsyncMock, llm_actor.node.invoke).assert_called_once()


async def test_actor_execute_llm_node_without_llm_raises(llm_node: LLMNode) -> None:
    actor = NodeActor(node=llm_node)  # No LLM provided
    inputs = "test"
    execution_id = uuid4()

    with pytest.raises(NodeActorError) as exc_info:
        await actor.execute(inputs, execution_id)

    assert "LLM required for LLMNode execution but not provided" in str(exc_info.value)


async def test_actor_execute_tool_node_success(tool_node: ToolNode) -> None:
    actor = NodeActor(node=tool_node)
    input_ = ToolCall.model_validate(
        {
            "name": "test_tool_node",
            "args": {"message": "hello"},
            "id": "test_call",
            "type": "tool_call",
        }
    )
    execution_id = uuid4()

    result = await actor.execute(input_, execution_id)

    assert isinstance(result, Result)
    assert result.output.content == "Tool response: hello"
    assert result.output.tool_call_id == "test_call"


async def test_actor_execute_node_exception_raises(
    llm_actor: NodeActor[LLMNode],
) -> None:
    llm_actor.node.invoke.side_effect = Exception("Node failed")  # type: ignore[attr-defined]
    inputs = "test"
    execution_id = uuid4()

    with pytest.raises(NodeActorError) as exc_info:
        await llm_actor.execute(inputs, execution_id)

    assert "Node execution failed" in str(exc_info.value)
    assert llm_actor.error is not None


def test_actor_composite_id_format(function_actor: NodeActor[FunctionNode]) -> None:
    composite_id = function_actor.composite_id
    parts = composite_id.split("/")

    assert parts[0] == "node_actor"
    assert parts[1] == "function_node"
    assert parts[2] == "test_function_node"
    assert parts[3] == str(function_actor.id)


def test_actor_serialize_state(llm_actor: NodeActor[LLMNode]) -> None:
    state = llm_actor.serialize_state()

    assert state["actor_id"] == str(llm_actor.id)
    assert state["node_id"] == str(llm_actor.node.id)
    assert state["status"] == NodeActorStatus.READY.value
    assert "node_state" in state
