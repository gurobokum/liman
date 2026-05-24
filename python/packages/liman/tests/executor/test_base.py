import asyncio
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from liman_core.node_actor.actor import NodeActor
from liman_core.node_actor.schemas import NextNode, Result
from liman_core.nodes.base.node import BaseNode
from liman_core.nodes.llm_node.node import LLMNode
from liman_core.nodes.tool_node.node import ToolNode
from liman_core.registry import Registry

from liman.executor.base import Executor, ParentExecutorPair
from liman.executor.schemas import ExecutorInput, ExecutorStatus
from liman.state import InMemoryStateStorage


@pytest.fixture
def llm_node(registry: Registry) -> LLMNode:
    node_dict = {
        "kind": "LLMNode",
        "name": "test_llm_node",
        "prompts": {
            "system": {"en": "You are a helpful assistant."},
        },
    }
    node = LLMNode.from_dict(node_dict, registry)
    node.compile()
    return node


@pytest.fixture
def node_actor(mock_llm: Mock, llm_node: LLMNode) -> NodeActor[LLMNode]:
    return NodeActor(llm_node, llm=mock_llm)


@pytest.fixture
def mock_llm() -> Mock:
    mock_llm = Mock(spec=BaseChatModel)
    mock_llm.invoke = AsyncMock()
    return mock_llm


def test_executor_init_basic(
    registry: Registry,
    storage: InMemoryStateStorage,
    mock_llm: Mock,
) -> None:
    executor = Executor(registry=registry, state_storage=storage, llm=mock_llm)

    assert isinstance(executor.id, UUID)
    assert isinstance(executor.execution_id, UUID)
    assert executor.max_iterations == 10
    assert executor.registry == registry
    assert executor.node_actors == {}
    assert executor.llm == mock_llm
    assert executor.status == ExecutorStatus.IDLE
    assert executor.iteration_count == 0
    assert executor.parent_executor_pair is None
    assert executor.child_executors == {}


def test_executor_init_with_execution_id(
    registry: Registry,
    storage: InMemoryStateStorage,
    mock_llm: Mock,
) -> None:
    execution_id = uuid4()
    executor = Executor(
        registry=registry,
        state_storage=storage,
        llm=mock_llm,
        execution_id=execution_id,
    )

    assert executor.execution_id == execution_id


def test_executor_init_with_max_iterations(
    registry: Registry,
    storage: InMemoryStateStorage,
    mock_llm: Mock,
) -> None:
    executor = Executor(
        registry=registry, state_storage=storage, llm=mock_llm, max_iterations=20
    )

    assert executor.max_iterations == 20


def test_executor_init_with_parent_pair(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    parent_executor = Executor(registry=registry, state_storage=storage, llm=mock_llm)
    pair = ParentExecutorPair(parent_executor, node_actor.id)
    child_executor = Executor(
        registry=registry,
        state_storage=storage,
        llm=mock_llm,
        parent_executor_pair=pair,
    )

    assert child_executor.parent_executor_pair == pair
    assert child_executor.is_child is True


def test_is_child_true(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    parent_executor = Executor(registry=registry, state_storage=storage, llm=mock_llm)
    pair = ParentExecutorPair(parent_executor, node_actor.id)
    child_executor = Executor(
        registry=registry,
        state_storage=storage,
        llm=mock_llm,
        parent_executor_pair=pair,
    )

    assert child_executor.is_child is True


def test_is_child_false(
    registry: Registry,
    storage: InMemoryStateStorage,
    mock_llm: Mock,
) -> None:
    executor = Executor(registry=registry, state_storage=storage, llm=mock_llm)

    assert executor.is_child is False


@pytest.mark.asyncio
async def test_step_basic_execution(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    execution_id = uuid4()
    executor = Executor(
        registry=registry,
        state_storage=storage,
        llm=mock_llm,
        execution_id=execution_id,
    )

    with (
        patch.object(
            executor,
            "_get_or_create_node_actor",
            new=AsyncMock(return_value=node_actor),
        ),
        patch.object(node_actor, "execute", new_callable=AsyncMock) as mock_execute,
    ):
        mock_execute.return_value = Result(output="test result", next_nodes=[])
        input_ = ExecutorInput(
            executor_id=executor.id,
            execution_id=execution_id,
            node_actor_id=node_actor.id,
            node_input="test input",
            node_fullname="LLMNode/test_llm_node",
        )
        result = await executor.step(input_)

    assert result.execution_id == execution_id
    assert result.node_actor_id == node_actor.id
    assert result.node_output == "test result"
    assert result.exit_ is True
    assert executor.status == ExecutorStatus.COMPLETED


@pytest.mark.asyncio
async def test_step_with_next_nodes_sequential(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    execution_id = uuid4()
    next_node = Mock(spec=ToolNode)
    next_node.full_name = "ToolNode/next"
    next_node_tuple = NextNode(next_node, "next input")

    executor = Executor(
        registry=registry,
        state_storage=storage,
        llm=mock_llm,
        execution_id=execution_id,
    )

    with (
        patch.object(
            executor,
            "_get_or_create_node_actor",
            new=AsyncMock(return_value=node_actor),
        ),
        patch.object(node_actor, "execute", new_callable=AsyncMock) as mock_execute,
    ):
        mock_execute.side_effect = [
            Result(output="intermediate", next_nodes=[next_node_tuple]),
            Result(output="final result", next_nodes=[]),
        ]
        input_ = ExecutorInput(
            executor_id=executor.id,
            execution_id=execution_id,
            node_actor_id=node_actor.id,
            node_input="test input",
            node_fullname="LLMNode/test_llm_node",
        )
        result = await executor.step(input_)

    assert result.node_output == "final result"
    assert result.exit_ is True
    assert executor.status == ExecutorStatus.COMPLETED
    assert mock_execute.call_count == 2


@pytest.mark.asyncio
async def test_step_max_iterations_exceeded(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    execution_id = uuid4()
    next_node = Mock(spec=ToolNode)
    next_node.full_name = "ToolNode/test"
    next_node_tuple = NextNode(next_node, "next input")

    executor = Executor(
        registry=registry,
        state_storage=storage,
        llm=mock_llm,
        execution_id=execution_id,
        max_iterations=2,
    )

    with (
        patch.object(
            executor,
            "_get_or_create_node_actor",
            new=AsyncMock(return_value=node_actor),
        ),
        patch.object(node_actor, "execute", new_callable=AsyncMock) as mock_execute,
    ):
        mock_execute.return_value = Result(output="loop", next_nodes=[next_node_tuple])
        input_ = ExecutorInput(
            executor_id=executor.id,
            execution_id=execution_id,
            node_actor_id=node_actor.id,
            node_input="test input",
            node_fullname="LLMNode/test_llm_node",
        )
        result = await executor.step(input_)

    assert executor.status == ExecutorStatus.FAILED
    assert executor.iteration_count == 2
    assert result.exit_ is True
    assert result.node_output is None


@pytest.mark.asyncio
async def test_execute_basic(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    execution_id = uuid4()
    executor = Executor(
        registry=registry,
        state_storage=storage,
        llm=mock_llm,
        execution_id=execution_id,
    )
    input_ = ExecutorInput(
        executor_id=executor.id,
        execution_id=execution_id,
        node_actor_id=node_actor.id,
        node_input="test input",
        node_fullname="LLMNode/test_llm_node",
    )

    with (
        patch.object(
            executor,
            "_get_or_create_node_actor",
            new=AsyncMock(return_value=node_actor),
        ),
        patch.object(node_actor, "execute", new_callable=AsyncMock) as mock_execute,
    ):
        mock_execute.return_value = Result(output="test result", next_nodes=[])
        result, returned_actor = await executor._execute(input_)

    mock_execute.assert_called_once_with(
        "test input", execution_id=execution_id, context=None
    )
    assert result.output == "test result"
    assert returned_actor is node_actor


@pytest.mark.asyncio
async def test_fork_executor(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    execution_id = uuid4()
    executor = Executor(
        registry=registry,
        state_storage=storage,
        llm=mock_llm,
        execution_id=execution_id,
    )

    next_node = Mock(spec=BaseNode)
    next_node.full_name = "LLMNode/next"

    child_executor = await executor._fork_executor(next_node, node_actor)

    assert isinstance(child_executor, Executor)
    assert child_executor.parent_executor_pair is not None
    assert child_executor.parent_executor_pair[0] is executor
    assert child_executor.parent_executor_pair[1] == node_actor.id
    assert child_executor.id in executor.child_executors
    assert executor.child_executors[child_executor.id] is child_executor
    assert child_executor.execution_id == execution_id


@pytest.mark.asyncio
async def test_handle_parallel_execution(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    executor = Executor(registry=registry, state_storage=storage, llm=mock_llm)

    node1 = Mock(spec=BaseNode)
    node1.full_name = "LLMNode/node1"
    node2 = Mock(spec=BaseNode)
    node2.full_name = "LLMNode/node2"
    next_nodes: list[NextNode] = [NextNode(node1, "input1"), NextNode(node2, "input2")]

    with patch.object(executor, "_fork_executor", new=AsyncMock()):
        await executor._handle_parallel_execution(next_nodes, node_actor)

    assert executor.status == ExecutorStatus.SUSPENDED


def test_on_exit_input_loop_cancelled_error(
    registry: Registry,
    storage: InMemoryStateStorage,
    mock_llm: Mock,
) -> None:
    executor = Executor(registry=registry, state_storage=storage, llm=mock_llm)

    cancelled_task = Mock()
    cancelled_task.result.side_effect = asyncio.CancelledError()

    executor._on_exit_input_loop(cancelled_task)

    assert executor._processing_task is None
