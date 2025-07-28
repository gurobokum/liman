import asyncio
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from dishka import AsyncContainer, Container

from liman_core.llm_node import LLMNode
from liman_core.node import Node
from liman_core.node_actor import NodeActorState
from liman_core.node_actor.actor import AsyncNodeActor
from liman_core.node_actor.errors import NodeActorError
from liman_core.tool_node import ToolNode


@pytest.fixture(scope="function")
def real_node(test_containers: tuple[Container, AsyncContainer]) -> Node:
    node_dict = {
        "kind": "Node",
        "name": "AsyncIntegrationTestNode",
        "func": "test_function",
        "description": {"en": "Test node for async integration"},
    }
    node = Node.from_dict(node_dict)
    node.compile()
    return node


@pytest.fixture(scope="function")
def real_llm_node(test_containers: tuple[Container, AsyncContainer]) -> LLMNode:
    node_dict = {
        "kind": "LLMNode",
        "name": "AsyncIntegrationLLMNode",
        "prompts": {"system": {"en": "You are a helpful assistant."}},
    }
    node = LLMNode.from_dict(node_dict)
    node.compile()
    return node


@pytest.fixture(scope="function")
def real_tool_node(
    test_containers: tuple[Container, AsyncContainer],
) -> ToolNode | None:
    node_dict = {
        "kind": "ToolNode",
        "name": "AsyncIntegrationToolNode",
        "tools": [{"name": "test_tool", "description": "A test tool"}],
    }
    try:
        node = ToolNode.from_dict(node_dict)
        node.compile()
        return node
    except Exception:
        pytest.skip("ToolNode dependencies not available")


async def test_async_actor_factory_pattern(real_node: Node) -> None:
    custom_id: UUID = uuid4()
    mock_llm = Mock()

    async_actor = AsyncNodeActor.create(
        node=real_node, actor_id=custom_id, llm=mock_llm
    )

    assert async_actor.id == custom_id
    assert async_actor.node is real_node
    assert async_actor.llm is mock_llm


async def test_async_actor_composite_id_format(real_node: Node) -> None:
    actor_id: UUID = uuid4()
    async_actor = AsyncNodeActor(node=real_node, actor_id=actor_id)

    async_composite = async_actor.composite_id
    async_parts = async_composite.split("/")

    assert len(async_parts) == 4
    assert async_parts[0] == "async_node_actor"
    assert async_parts[1] == "node"
    assert async_parts[2] == "AsyncIntegrationTestNode"
    assert async_parts[3] == str(actor_id)


async def test_async_actor_status_format(real_node: Node) -> None:
    async_actor = AsyncNodeActor(node=real_node)

    async_status = async_actor.get_status()

    expected_keys = {"actor_id", "node_name", "node_type", "state", "is_shutdown"}
    assert set(async_status.keys()) == expected_keys
    assert async_status["node_name"] == "AsyncIntegrationTestNode"
    assert async_status["node_type"] == "Node"
    assert async_status["state"] == NodeActorState.IDLE


async def test_async_actor_lifecycle(real_node: Node) -> None:
    async_actor = AsyncNodeActor(node=real_node)

    assert async_actor.state == NodeActorState.IDLE

    await async_actor.initialize()
    assert async_actor.state == NodeActorState.READY

    await async_actor.shutdown()
    assert async_actor.state == NodeActorState.SHUTDOWN


async def test_async_actor_execution_context(real_node: Node) -> None:
    execution_id: UUID = uuid4()
    context = {"custom_key": "custom_value"}

    async_actor = AsyncNodeActor(node=real_node)
    async_ctx = async_actor._prepare_execution_context(context, execution_id)

    assert async_ctx["custom_key"] == "custom_value"
    assert async_ctx["actor_id"] == async_actor.id
    assert async_ctx["execution_id"] == execution_id
    assert async_ctx["node_name"] == "AsyncIntegrationTestNode"
    assert async_ctx["node_type"] == "Node"


async def test_async_actor_validation_consistency(real_llm_node: LLMNode) -> None:
    async_actor = AsyncNodeActor(node=real_llm_node)

    with pytest.raises(NodeActorError):
        await async_actor._validate_requirements()

    # Should pass validation with LLM
    mock_llm = Mock()
    async_actor_with_llm = AsyncNodeActor(node=real_llm_node, llm=mock_llm)
    await async_actor_with_llm._validate_requirements()  # Should not raise


async def test_async_actor_node_type_detection(
    real_node: Node, real_llm_node: LLMNode
) -> None:
    async_actor = AsyncNodeActor(node=real_node)

    assert not async_actor.node.is_llm_node
    assert not async_actor.node.is_tool_node

    async_llm_actor = AsyncNodeActor(node=real_llm_node)

    assert async_llm_actor.node.is_llm_node
    assert not async_llm_actor.node.is_tool_node


async def test_async_actor_repr_consistency(real_node: Node) -> None:
    actor_id: UUID = uuid4()
    async_actor = AsyncNodeActor(node=real_node, actor_id=actor_id)

    async_repr = repr(async_actor)

    assert str(actor_id) in async_repr
    assert "AsyncIntegrationTestNode" in async_repr
    assert NodeActorState.IDLE in async_repr
    assert "AsyncNodeActor" in async_repr


async def test_async_actor_multiple_instances(real_node: Node) -> None:
    actors = [
        AsyncNodeActor(node=real_node),
        AsyncNodeActor(node=real_node),
        AsyncNodeActor(node=real_node),
    ]

    # Initialize all
    for actor in actors:
        await actor.initialize()

    # All should be ready
    for actor in actors:
        assert actor.state == NodeActorState.READY

    # Shutdown all
    for actor in actors:
        await actor.shutdown()

    # All should be shutdown
    for actor in actors:
        assert actor.state == NodeActorState.SHUTDOWN


async def test_async_actor_multiple_instances_concurrent(real_node: Node) -> None:
    actors = [
        AsyncNodeActor(node=real_node),
        AsyncNodeActor(node=real_node),
        AsyncNodeActor(node=real_node),
    ]

    # Initialize all concurrently
    await asyncio.gather(*[actor.initialize() for actor in actors])

    # All should be ready
    for actor in actors:
        assert actor.state == NodeActorState.READY

    # Shutdown all concurrently
    await asyncio.gather(*[actor.shutdown() for actor in actors])

    # All should be shutdown
    for actor in actors:
        assert actor.state == NodeActorState.SHUTDOWN
