from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from liman_core.base import Output
from liman_core.llm_node import LLMNode
from liman_core.node import Node
from liman_core.node_actor import AsyncNodeActor, NodeActorError, NodeActorStatus
from liman_core.tool_node import ToolNode


@pytest.fixture
def mock_node() -> Mock:
    node = Mock(spec=Node)
    node.name = "test_node"
    node.spec.kind = "Node"
    node._compiled = True
    node.is_llm_node = False
    node.is_tool_node = False
    node.ainvoke = AsyncMock(return_value=Output(response=AIMessage("test_result")))
    return node


@pytest.fixture
def mock_llm_node() -> Mock:
    node = Mock(spec=LLMNode)
    node.name = "llm_test_node"
    node.spec.kind = "LLMNode"
    node._compiled = True
    node.is_llm_node = True
    node.is_tool_node = False
    node.ainvoke = AsyncMock(return_value=Output(response=AIMessage("llm_result")))
    return node


@pytest.fixture
def mock_tool_node() -> Mock:
    node = Mock(spec=ToolNode)
    node.name = "tool_test_node"
    node.spec.kind = "ToolNode"
    node._compiled = True
    node.is_llm_node = False
    node.is_tool_node = True
    node.ainvoke = AsyncMock(return_value=Output(response=AIMessage("tool_result")))
    return node


@pytest.fixture
def mock_llm() -> Mock:
    return Mock()


@pytest.fixture
async def async_actor(mock_node: Mock) -> AsyncNodeActor:
    return AsyncNodeActor(node=mock_node)


async def test_async_actor_create_method(mock_node: Mock) -> None:
    actor = AsyncNodeActor.create(node=mock_node)

    assert isinstance(actor, AsyncNodeActor)
    assert actor.node is mock_node
    assert actor.status == NodeActorStatus.IDLE


async def test_async_actor_initialize_success(async_actor: AsyncNodeActor) -> None:
    await async_actor.initialize()

    assert async_actor.status == NodeActorStatus.READY


async def test_async_actor_initialize_wrong_status_raises(
    async_actor: AsyncNodeActor,
) -> None:
    async_actor.status = NodeActorStatus.READY

    with pytest.raises(NodeActorError) as exc_info:
        await async_actor.initialize()

    assert "Cannot initialize actor in status" in str(exc_info.value)


async def test_async_actor_initialize_uncompiled_node_raises(mock_node: Mock) -> None:
    mock_node._compiled = False
    actor = AsyncNodeActor(node=mock_node)

    with pytest.raises(NodeActorError) as exc_info:
        await actor.initialize()

    assert "Failed to initialize actor" in str(exc_info.value)
    assert actor.error is not None


async def test_async_actor_execute_success(async_actor: AsyncNodeActor) -> None:
    await async_actor.initialize()
    inputs = [HumanMessage(content="test")]

    result = await async_actor.execute(inputs)

    assert result.response.content == "test_result"
    assert async_actor.status == NodeActorStatus.COMPLETED


async def test_async_actor_execute_wrong_status_raises(
    async_actor: AsyncNodeActor,
) -> None:
    inputs = [HumanMessage(content="test")]

    with pytest.raises(NodeActorError) as exc_info:
        await async_actor.execute(inputs)

    assert "Cannot execute actor in status" in str(exc_info.value)


async def test_async_actor_execute_after_shutdown_raises(
    async_actor: AsyncNodeActor,
) -> None:
    await async_actor.initialize()
    await async_actor.shutdown()
    inputs = [HumanMessage(content="test")]

    with pytest.raises(NodeActorError) as exc_info:
        await async_actor.execute(inputs)

    assert "Cannot execute actor in status shutdown" in str(exc_info.value)


async def test_async_actor_execute_with_context(async_actor: AsyncNodeActor) -> None:
    await async_actor.initialize()
    inputs = [HumanMessage(content="test")]
    context = {"custom_key": "custom_value"}
    execution_id: UUID = uuid4()

    await async_actor.execute(inputs, context=context, execution_id=execution_id)

    call_kwargs = async_actor.node.ainvoke.call_args[1]  # type: ignore
    assert call_kwargs["custom_key"] == "custom_value"
    assert call_kwargs["actor_id"] == async_actor.id
    assert call_kwargs["execution_id"] == execution_id


async def test_async_actor_execute_llm_node_success(
    mock_llm_node: Mock, mock_llm: Mock
) -> None:
    actor = AsyncNodeActor(node=mock_llm_node, llm=mock_llm)
    await actor.initialize()
    inputs = [HumanMessage(content="test")]

    result = await actor.execute(inputs)

    assert result.response.content == "llm_result"
    mock_llm_node.ainvoke.assert_called_once()
    call_args = mock_llm_node.ainvoke.call_args
    assert call_args[0][0] is mock_llm  # First positional arg should be LLM


async def test_async_actor_execute_llm_node_without_llm_raises(
    mock_llm_node: Mock,
) -> None:
    actor = AsyncNodeActor(node=mock_llm_node)

    with pytest.raises(NodeActorError) as exc_info:
        await actor.initialize()

    assert "LLMNode requires LLM but none provided" in str(exc_info.value)


async def test_async_actor_execute_tool_node_success(mock_tool_node: Mock) -> None:
    actor = AsyncNodeActor(node=mock_tool_node)
    await actor.initialize()
    inputs = [HumanMessage(content="test")]

    result = await actor.execute(inputs)

    assert result.response.content == "tool_result"
    mock_tool_node.ainvoke.assert_called_once()


async def test_async_actor_execute_node_exception_raises(
    async_actor: AsyncNodeActor,
) -> None:
    await async_actor.initialize()
    async_actor.node.ainvoke.side_effect = Exception("Node failed")  # type: ignore
    inputs = [HumanMessage(content="test")]

    with pytest.raises(NodeActorError) as exc_info:
        await async_actor.execute(inputs)

    assert "Node execution failed" in str(exc_info.value)
    assert async_actor.error is not None


async def test_async_actor_shutdown(async_actor: AsyncNodeActor) -> None:
    await async_actor.shutdown()

    assert async_actor.status == NodeActorStatus.SHUTDOWN
    assert async_actor._is_shutdown()


async def test_async_actor_composite_id_format(async_actor: AsyncNodeActor) -> None:
    composite_id = async_actor.composite_id
    parts = composite_id.split("/")

    assert parts[0] == "async_node_actor"
    assert parts[1] == "node"
    assert parts[2] == "test_node"
    assert parts[3] == str(async_actor.id)
