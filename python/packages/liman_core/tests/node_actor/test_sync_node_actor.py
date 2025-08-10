import threading
from typing import cast
from unittest.mock import Mock
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from liman_core.base.schemas import S
from liman_core.node_actor import NodeActor, NodeActorError, NodeActorStatus
from liman_core.node_actor.schemas import Result
from liman_core.nodes.base.schemas import NS, NodeOutput
from liman_core.nodes.llm_node import LLMNode
from liman_core.nodes.llm_node.schemas import LLMNodeState
from liman_core.nodes.node import Node
from liman_core.nodes.node.schemas import NodeSpec, NodeState
from liman_core.nodes.tool_node import ToolNode
from liman_core.registry import Registry


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
    node.invoke = Mock(return_value=NodeOutput(response=AIMessage("test_result")))
    return cast(Node, node)


@pytest.fixture
def mock_llm_node(registry: Registry) -> LLMNode:
    node = Mock(spec=LLMNode)
    node.name = "llm_test_node"
    node.id = uuid4()
    node.spec.kind = "LLMNode"
    node._compiled = True
    node.is_llm_node = True
    node.is_tool_node = False
    node.get_new_state.return_value = LLMNodeState()
    node.invoke = Mock(return_value=NodeOutput(response=AIMessage("llm_result")))
    node.registry = registry
    return cast(LLMNode, node)


@pytest.fixture
def mock_tool_node(registry: Registry) -> ToolNode:
    node = Mock(spec=ToolNode)
    node.name = "tool_test_node"
    node.id = uuid4()
    node.spec.kind = "ToolNode"
    node._compiled = True
    node.is_llm_node = False
    node.is_tool_node = True
    node.get_new_state.return_value = NodeState()
    node.invoke = Mock(return_value=NodeOutput(response=AIMessage("tool_result")))
    node.registry = registry
    return cast(ToolNode, node)


@pytest.fixture
def mock_llm() -> Mock:
    return Mock()


@pytest.fixture
def sync_actor(mock_node: Node, registry: Registry) -> NodeActor[NodeSpec, NodeState]:
    mock_node.registry = registry
    return NodeActor(node=mock_node)


def test_sync_actor_create_method(mock_node: Node) -> None:
    actor = NodeActor.create(node=mock_node)

    assert isinstance(actor, NodeActor)
    assert actor.node is mock_node
    assert actor.status == NodeActorStatus.IDLE


def test_sync_actor_initialize_success(sync_actor: NodeActor[S, NS]) -> None:
    sync_actor.initialize()

    assert sync_actor.status == NodeActorStatus.READY


def test_sync_actor_initialize_wrong_status_raises(
    sync_actor: NodeActor[S, NS],
) -> None:
    sync_actor.state.status = NodeActorStatus.READY

    with pytest.raises(NodeActorError) as exc_info:
        sync_actor.initialize()

    assert "Cannot initialize actor in status" in str(exc_info.value)


def test_sync_actor_initialize_uncompiled_node_raises(mock_node: Node) -> None:
    mock_node._compiled = False
    actor = NodeActor(node=mock_node)

    with pytest.raises(NodeActorError) as exc_info:
        actor.initialize()

    assert "Failed to initialize actor" in str(exc_info.value)
    assert actor.error is not None


def test_sync_actor_execute_success(sync_actor: NodeActor[S, NS]) -> None:
    sync_actor.initialize()
    inputs = [HumanMessage(content="test")]
    execution_id = uuid4()

    result = sync_actor.execute(inputs, execution_id)

    assert result.node_output.response.content == "test_result"
    assert sync_actor.status == NodeActorStatus.COMPLETED


def test_sync_actor_execute_wrong_status_raises(sync_actor: NodeActor[S, NS]) -> None:
    inputs = [HumanMessage(content="test")]
    execution_id = uuid4()

    with pytest.raises(NodeActorError) as exc_info:
        sync_actor.execute(inputs, execution_id)

    assert "Cannot execute actor in status" in str(exc_info.value)


def test_sync_actor_execute_after_shutdown_raises(sync_actor: NodeActor[S, NS]) -> None:
    sync_actor.initialize()
    sync_actor.shutdown()
    inputs = [HumanMessage(content="test")]
    execution_id = uuid4()

    with pytest.raises(NodeActorError) as exc_info:
        sync_actor.execute(inputs, execution_id)

    assert "Cannot execute actor in status shutdown" in str(exc_info.value)


def test_sync_actor_execute_with_context(sync_actor: NodeActor[S, NS]) -> None:
    sync_actor.initialize()
    inputs = [HumanMessage(content="test")]
    context = {"custom_key": "custom_value"}
    execution_id = uuid4()

    sync_actor.execute(inputs, context=context, execution_id=execution_id)

    call_kwargs = sync_actor.node.invoke.call_args[1]  # type: ignore[attr-defined]
    assert call_kwargs["custom_key"] == "custom_value"
    assert call_kwargs["actor_id"] == sync_actor.id
    assert call_kwargs["execution_id"] == execution_id


def test_sync_actor_execute_llm_node_success(
    mock_llm_node: LLMNode, mock_llm: Mock
) -> None:
    actor = NodeActor(node=mock_llm_node, llm=mock_llm)
    actor.initialize()
    inputs = [HumanMessage(content="test")]
    execution_id = uuid4()

    result = actor.execute(inputs, execution_id)

    assert result.node_output.response.content == "llm_result"
    mock_invoke = cast(Mock, mock_llm_node.invoke)
    mock_invoke.assert_called_once()
    call_args = mock_invoke.call_args
    assert call_args[0][0] is mock_llm  # First positional arg should be LLM


def test_sync_actor_execute_llm_node_without_llm_raises(mock_llm_node: LLMNode) -> None:
    actor = NodeActor(node=mock_llm_node)

    with pytest.raises(NodeActorError) as exc_info:
        actor.initialize()

    assert "LLMNode requires LLM but none provided" in str(exc_info.value)


def test_sync_actor_execute_tool_node_success(mock_tool_node: ToolNode) -> None:
    actor = NodeActor(node=mock_tool_node)
    actor.initialize()
    inputs = [HumanMessage(content="test")]
    execution_id = uuid4()

    result = actor.execute(inputs, execution_id)

    assert result.node_output.response.content == "tool_result"
    mock_invoke = cast(Mock, mock_tool_node.invoke)
    mock_invoke.assert_called_once()


def test_sync_actor_execute_node_exception_raises(sync_actor: NodeActor[S, NS]) -> None:
    sync_actor.initialize()
    sync_actor.node.invoke.side_effect = Exception("Node failed")  # type: ignore[attr-defined]
    inputs = [HumanMessage(content="test")]
    execution_id = uuid4()

    with pytest.raises(NodeActorError) as exc_info:
        sync_actor.execute(inputs, execution_id)

    assert "Node execution failed" in str(exc_info.value)
    assert sync_actor.error is not None


def test_sync_actor_shutdown(sync_actor: NodeActor[S, NS]) -> None:
    sync_actor.shutdown()

    assert sync_actor.status == NodeActorStatus.SHUTDOWN
    assert sync_actor._is_shutdown()


def test_sync_actor_composite_id_format(sync_actor: NodeActor[S, NS]) -> None:
    composite_id = sync_actor.composite_id
    parts = composite_id.split("/")

    assert parts[0] == "node_actor"
    assert parts[1] == "node"
    assert parts[2] == "test_node"
    assert parts[3] == str(sync_actor.id)


def test_sync_actor_threading_safety(sync_actor: NodeActor[S, NS]) -> None:
    sync_actor.initialize()
    inputs = [HumanMessage(content="test")]

    executed = []

    def execute_multiple() -> None:
        for _ in range(5):
            try:
                execution_id = uuid4()
                result = sync_actor.execute(inputs, execution_id)
                executed.append(result)
            except Exception:
                ...

    threads = [threading.Thread(target=execute_multiple) for _ in range(3)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert len(executed) == 5 * 3
    assert all(isinstance(r, Result) for r in executed)
