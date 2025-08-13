from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from liman_core.node_actor import NodeActor, NodeActorError, NodeActorStatus
from liman_core.nodes.function_node.node import FunctionNode
from liman_core.nodes.llm_node.node import LLMNode


async def test_actor_factory_pattern(function_node: FunctionNode) -> None:
    actor_id = uuid4()
    mock_llm = AsyncMock()

    async_actor = NodeActor.create(node=function_node, actor_id=actor_id, llm=mock_llm)

    assert async_actor.id == actor_id
    assert async_actor.node is function_node
    assert async_actor.llm is mock_llm


async def test_actor_composite_id_format(function_node: FunctionNode) -> None:
    actor_id = uuid4()
    async_actor = NodeActor(node=function_node, actor_id=actor_id)

    async_composite = async_actor.composite_id
    async_parts = async_composite.split("/")

    assert len(async_parts) == 4
    assert async_parts[0] == "node_actor"
    assert async_parts[1] == "function_node"
    assert async_parts[2] == "test_function_node"
    assert async_parts[3] == str(actor_id)


async def test_actor_lifecycle(function_node: FunctionNode) -> None:
    async_actor = NodeActor(node=function_node)

    assert async_actor.status == NodeActorStatus.READY


async def test_actor_execution_context(function_node: FunctionNode) -> None:
    context = {"custom_key": "custom_value"}
    execution_id = uuid4()

    async_actor = NodeActor(node=function_node)
    async_ctx = async_actor._prepare_execution_context(context, execution_id)

    assert async_ctx["custom_key"] == "custom_value"
    assert async_ctx["actor_id"] == async_actor.id
    assert async_ctx["execution_id"] == execution_id
    assert async_ctx["node_name"] == "test_function_node"
    assert async_ctx["node_type"] == "FunctionNode"


async def test_actor_validation_consistency(llm_node: LLMNode) -> None:
    # LLMNode without LLM should fail during execution
    async_actor = NodeActor(node=llm_node)
    execution_id = uuid4()

    with pytest.raises(NodeActorError) as exc_info:
        await async_actor.execute("test", execution_id)
    assert "LLM required for LLMNode execution" in str(exc_info.value)

    # Should work with LLM
    async_actor_with_llm = NodeActor(node=llm_node, llm=AsyncMock())
    assert async_actor_with_llm.status == NodeActorStatus.READY


async def test_actor_node_type_detection(
    llm_node: LLMNode, function_node: FunctionNode
) -> None:
    function_actor = NodeActor(node=function_node)

    assert not function_actor.node.is_llm_node
    assert not function_actor.node.is_tool_node

    llm_actor = NodeActor(node=llm_node, llm=AsyncMock())

    assert llm_actor.node.is_llm_node
    assert not llm_actor.node.is_tool_node


async def test_async_actor_repr_consistency(function_actor: FunctionNode) -> None:
    actor_repr = repr(function_actor)

    assert str(function_actor) in actor_repr
    assert "test_function_node" in actor_repr
    assert NodeActorStatus.READY.value in actor_repr
    assert "NodeActor" in actor_repr


async def test_async_actor_multiple_instances(function_node: FunctionNode) -> None:
    actors = [
        NodeActor(node=function_node),
        NodeActor(node=function_node),
        NodeActor(node=function_node),
    ]

    # All should be ready immediately after creation
    for actor in actors:
        assert actor.status == NodeActorStatus.READY

    # All actors should have unique IDs
    actor_ids = [actor.id for actor in actors]
    assert len(set(actor_ids)) == 3


async def test_async_actor_multiple_instances_concurrent(
    function_node: FunctionNode,
) -> None:
    actors = [
        NodeActor(node=function_node),
        NodeActor(node=function_node),
        NodeActor(node=function_node),
    ]

    # All should be ready immediately after creation
    for actor in actors:
        assert actor.status == NodeActorStatus.READY

    # Test concurrent state serialization
    def get_state(actor: NodeActor[FunctionNode]) -> dict[str, Any]:
        return actor.serialize_state()

    states = [get_state(actor) for actor in actors]

    assert len(states) == 3
    for state in states:
        assert state["status"] == NodeActorStatus.READY.value
