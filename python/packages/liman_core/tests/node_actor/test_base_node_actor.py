from typing import Any
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from liman_core.node import Node
from liman_core.node_actor import NodeActorState
from liman_core.node_actor.actor import BaseNodeActor, create_error
from liman_core.node_actor.errors import NodeActorError


class MockNodeActor(BaseNodeActor):
    """
    Concrete implementation of BaseNodeActor for testing
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._shutdown = False

    def initialize(self) -> None:
        self.state = NodeActorState.READY

    def execute(
        self,
        inputs: Any,
        context: dict[str, Any] | None = None,
        execution_id: UUID | None = None,
    ) -> Mock:
        return Mock()

    def shutdown(self) -> None:
        self._shutdown = True

    def _is_shutdown(self) -> bool:
        return self._shutdown


@pytest.fixture
def mock_node() -> Mock:
    """
    Create a mock node for testing
    """
    node = Mock(spec=Node)
    node.name = "test_node"
    node.spec.kind = "Node"
    node._compiled = True
    node.is_llm_node = False
    node.is_tool_node = False
    return node


@pytest.fixture
def test_actor(mock_node: Mock) -> MockNodeActor:
    """
    Create a test actor instance
    """
    return MockNodeActor(node=mock_node)


def test_actor_initialization(mock_node: Mock) -> None:
    actor = MockNodeActor(node=mock_node)

    assert actor.node is mock_node
    assert actor.llm is None
    assert actor.state == NodeActorState.IDLE
    assert actor.error is None
    assert actor.id is not None


def test_actor_initialization_with_custom_id(mock_node: Mock) -> None:
    custom_id: UUID = uuid4()
    actor = MockNodeActor(node=mock_node, actor_id=custom_id)

    assert actor.id == custom_id


def test_actor_initialization_with_llm(mock_node: Mock) -> None:
    mock_llm = Mock()
    actor = MockNodeActor(node=mock_node, llm=mock_llm)

    assert actor.llm is mock_llm


def test_composite_id_format(test_actor: MockNodeActor) -> None:
    composite_id = test_actor.composite_id

    parts = composite_id.split("/")
    assert len(parts) == 4
    assert parts[0] == "mock_node_actor"
    assert parts[1] == "node"
    assert parts[2] == "test_node"
    assert parts[3] == str(test_actor.id)


def test_get_status_returns_expected_fields(test_actor: MockNodeActor) -> None:
    status = test_actor.get_status()

    expected_keys = {"actor_id", "node_name", "node_type", "state", "is_shutdown"}
    assert set(status.keys()) == expected_keys
    assert status["actor_id"] == str(test_actor.id)
    assert status["node_name"] == "test_node"
    assert status["node_type"] == "Node"
    assert status["state"] == NodeActorState.IDLE
    assert status["is_shutdown"] is False


def test_get_status_after_shutdown(test_actor: MockNodeActor) -> None:
    test_actor.shutdown()
    status = test_actor.get_status()

    assert status["is_shutdown"] is True


def test_prepare_execution_context(test_actor: MockNodeActor) -> None:
    execution_id: UUID = uuid4()
    context = {"custom_key": "custom_value"}

    result = test_actor._prepare_execution_context(context, execution_id)

    assert result["custom_key"] == "custom_value"
    assert result["actor_id"] == test_actor.id
    assert result["execution_id"] == execution_id
    assert result["node_name"] == "test_node"
    assert result["node_type"] == "Node"


def test_prepare_execution_context_with_llm(mock_node: Mock) -> None:
    mock_llm = Mock()
    actor = MockNodeActor(node=mock_node, llm=mock_llm)
    execution_id: UUID = uuid4()
    context: dict[str, Any] = {}

    result = actor._prepare_execution_context(context, execution_id)

    assert result["llm"] is mock_llm


def test_prepare_execution_context_doesnt_override_llm(mock_node: Mock) -> None:
    mock_llm = Mock()
    context_llm = Mock()
    actor = MockNodeActor(node=mock_node, llm=mock_llm)
    execution_id: UUID = uuid4()
    context = {"llm": context_llm}

    result = actor._prepare_execution_context(context, execution_id)

    assert result["llm"] is context_llm


def test_create_error_helper(test_actor: MockNodeActor) -> None:
    execution_id: UUID = uuid4()
    error = create_error("Test error", test_actor, execution_id=execution_id)

    assert isinstance(error, NodeActorError)
    assert str(error) == "Test error"
    assert error["actor_id"] == test_actor.id
    assert error.code == "node_actor_error"
    assert error["actor_composite_id"] == test_actor.composite_id
    assert error["node_kind"] == "Node"
    assert error["node_name"] == "test_node"
    assert error["execution_id"] == execution_id


def test_repr_format(test_actor: MockNodeActor) -> None:
    repr_str = repr(test_actor)

    assert "MockNodeActor" in repr_str
    assert str(test_actor.id) in repr_str
    assert "test_node" in repr_str
    assert NodeActorState.IDLE in repr_str
