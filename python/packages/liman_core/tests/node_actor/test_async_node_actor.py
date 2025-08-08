from typing import cast
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from liman_core.base import NodeOutput
from liman_core.base.schemas import NS, S
from liman_core.llm_node import LLMNode
from liman_core.llm_node.schemas import LLMNodeState
from liman_core.node import Node
from liman_core.node.schemas import NodeSpec, NodeState
from liman_core.node_actor import NodeActor, NodeActorError, NodeActorStatus
from liman_core.tool_node import ToolNode


@pytest.fixture
def mock_node() -> Node:
    node = Mock(spec=Node)
    node.name = "test_node"
    node.id = uuid4()
    node.spec.kind = "Node"
    node._compiled = True
    node.is_llm_node = False
    node.is_tool_node = False
    node.get_new_state.return_value = NodeState()
    node.ainvoke = AsyncMock(return_value=NodeOutput(response=AIMessage("test_result")))
    node.spec.nodes = []
    node.spec.llm_nodes = []
    return cast(Node, node)


@pytest.fixture
def mock_llm_node() -> LLMNode:
    node = Mock(spec=LLMNode)
    node.name = "llm_test_node"
    node.id = uuid4()
    node.spec.kind = "LLMNode"
    node._compiled = True
    node.is_llm_node = True
    node.is_tool_node = False
    node.get_new_state.return_value = LLMNodeState()
    node.ainvoke = AsyncMock(return_value=NodeOutput(response=AIMessage("llm_result")))
    node.spec.nodes = []
    return cast(LLMNode, node)


@pytest.fixture
def mock_tool_node() -> ToolNode:
    node = Mock(spec=ToolNode)
    node.name = "tool_test_node"
    node.id = uuid4()
    node.spec.kind = "ToolNode"
    node._compiled = True
    node.is_llm_node = False
    node.is_tool_node = True
    node.get_new_state.return_value = NodeState()
    node.ainvoke = AsyncMock(return_value=NodeOutput(response=AIMessage("tool_result")))
    node.spec.nodes = []
    node.spec.llm_nodes = []
    return cast(ToolNode, node)


@pytest.fixture
def mock_llm() -> Mock:
    return Mock()


@pytest.fixture
def async_actor(mock_node: Node) -> NodeActor[NodeSpec, NodeState]:
    return NodeActor(node=mock_node)


async def test_async_actor_create_method(mock_node: Node) -> None:
    actor = NodeActor.create(node=mock_node)

    assert isinstance(actor, NodeActor)
    assert actor.node is mock_node
    assert actor.status == NodeActorStatus.IDLE


async def test_async_actor_initialize_success(async_actor: NodeActor[S, NS]) -> None:
    await async_actor.ainitialize()

    assert async_actor.status == NodeActorStatus.READY


async def test_async_actor_initialize_wrong_status_raises(
    async_actor: NodeActor[S, NS],
) -> None:
    async_actor.state.status = NodeActorStatus.READY

    with pytest.raises(NodeActorError) as exc_info:
        await async_actor.ainitialize()

    assert "Cannot initialize actor in status" in str(exc_info.value)


async def test_async_actor_initialize_uncompiled_node_raises(mock_node: Node) -> None:
    mock_node._compiled = False
    actor = NodeActor(node=mock_node)

    with pytest.raises(NodeActorError) as exc_info:
        await actor.ainitialize()

    assert "Failed to initialize actor" in str(exc_info.value)
    assert actor.error is not None


async def test_async_actor_execute_success(async_actor: NodeActor[S, NS]) -> None:
    await async_actor.ainitialize()
    inputs = [HumanMessage(content="test")]
    execution_id = uuid4()

    result = await async_actor.aexecute(inputs, execution_id)

    assert result.node_output.response.content == "test_result"
    assert async_actor.status == NodeActorStatus.COMPLETED


async def test_async_actor_execute_wrong_status_raises(
    async_actor: NodeActor[S, NS],
) -> None:
    inputs = [HumanMessage(content="test")]
    execution_id = uuid4()

    with pytest.raises(NodeActorError) as exc_info:
        await async_actor.aexecute(inputs, execution_id)

    assert "Cannot execute actor in status" in str(exc_info.value)


async def test_async_actor_execute_after_shutdown_raises(
    async_actor: NodeActor[S, NS],
) -> None:
    await async_actor.ainitialize()
    await async_actor.ashutdown()
    inputs = [HumanMessage(content="test")]
    execution_id = uuid4()

    with pytest.raises(NodeActorError) as exc_info:
        await async_actor.aexecute(inputs, execution_id)

    assert "Cannot execute actor in status shutdown" in str(exc_info.value)


async def test_async_actor_execute_with_context(async_actor: NodeActor[S, NS]) -> None:
    await async_actor.ainitialize()
    inputs = [HumanMessage(content="test")]
    context = {"custom_key": "custom_value"}
    execution_id = uuid4()

    await async_actor.aexecute(inputs, context=context, execution_id=execution_id)

    call_kwargs = async_actor.node.ainvoke.call_args[1]  # type: ignore[attr-defined]
    assert call_kwargs["custom_key"] == "custom_value"
    assert call_kwargs["actor_id"] == async_actor.id
    assert call_kwargs["execution_id"] == execution_id


async def test_async_actor_execute_llm_node_success(
    mock_llm_node: LLMNode, mock_llm: Mock
) -> None:
    actor = NodeActor(node=mock_llm_node, llm=mock_llm)
    await actor.ainitialize()
    inputs = [HumanMessage(content="test")]
    execution_id = uuid4()

    result = await actor.aexecute(inputs, execution_id)

    assert result.node_output.response.content == "llm_result"
    mock_ainvoke = cast(Mock, mock_llm_node.ainvoke)
    mock_ainvoke.assert_called_once()
    call_args = mock_ainvoke.call_args
    assert call_args[0][0] is mock_llm  # First positional arg should be LLM


async def test_async_actor_execute_llm_node_without_llm_raises(
    mock_llm_node: LLMNode,
) -> None:
    actor = NodeActor(node=mock_llm_node)

    with pytest.raises(NodeActorError) as exc_info:
        await actor.ainitialize()

    assert "LLMNode requires LLM but none provided" in str(exc_info.value)


async def test_async_actor_execute_tool_node_success(mock_tool_node: ToolNode) -> None:
    actor = NodeActor(node=mock_tool_node)
    await actor.ainitialize()
    inputs = [HumanMessage(content="test")]
    execution_id = uuid4()

    result = await actor.aexecute(inputs, execution_id)

    assert result.node_output.response.content == "tool_result"
    mock_ainvoke = cast(Mock, mock_tool_node.ainvoke)
    mock_ainvoke.assert_called_once()


async def test_async_actor_execute_node_exception_raises(
    async_actor: NodeActor[S, NS],
) -> None:
    await async_actor.ainitialize()
    async_actor.node.ainvoke.side_effect = Exception("Node failed")  # type: ignore[attr-defined]
    inputs = [HumanMessage(content="test")]
    execution_id = uuid4()

    with pytest.raises(NodeActorError) as exc_info:
        await async_actor.aexecute(inputs, execution_id)

    assert "Node execution failed" in str(exc_info.value)
    assert async_actor.error is not None


async def test_async_actor_shutdown(async_actor: NodeActor[S, NS]) -> None:
    await async_actor.ashutdown()

    assert async_actor.status == NodeActorStatus.SHUTDOWN
    assert async_actor._is_async_shutdown()


async def test_async_actor_composite_id_format(async_actor: NodeActor[S, NS]) -> None:
    composite_id = async_actor.composite_id
    parts = composite_id.split("/")

    assert parts[0] == "node_actor"
    assert parts[1] == "node"
    assert parts[2] == "test_node"
    assert parts[3] == str(async_actor.id)
