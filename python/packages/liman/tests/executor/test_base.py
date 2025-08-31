import asyncio
from asyncio import Queue
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

from liman.executor.base import Executor
from liman.executor.schemas import ExecutorInput, ExecutorOutput, ExecutorStatus
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
    mock_actor = NodeActor(llm_node, llm=mock_llm)
    return mock_actor


@pytest.fixture
def mock_llm() -> Mock:
    mock_llm = Mock(spec=BaseChatModel)
    mock_llm.invoke = AsyncMock()
    return mock_llm


def test_executor_init_basic(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    executor = Executor(
        registry=registry,
        state_storage=storage,
        node_actor=node_actor,
        llm=mock_llm,
    )

    assert isinstance(executor.id, UUID)
    assert isinstance(executor.execution_id, UUID)
    assert executor.max_iterations == 10
    assert executor.registry == registry
    assert executor.node_actor == node_actor
    assert executor.llm == mock_llm
    assert executor.status == ExecutorStatus.IDLE
    assert executor.iteration_count == 0
    assert executor.parent_executor is None
    assert executor.child_executors == {}


def test_executor_init_with_execution_id(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    execution_id = uuid4()
    executor = Executor(
        registry=registry,
        state_storage=storage,
        node_actor=node_actor,
        llm=mock_llm,
        execution_id=execution_id,
    )

    assert executor.execution_id == execution_id


def test_executor_init_with_max_iterations(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    max_iterations = 20
    executor = Executor(
        registry=registry,
        state_storage=storage,
        node_actor=node_actor,
        llm=mock_llm,
        max_iterations=max_iterations,
    )

    assert executor.max_iterations == max_iterations


def test_executor_init_with_parent(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    parent_executor = Executor(
        registry=registry,
        state_storage=storage,
        node_actor=node_actor,
        llm=mock_llm,
    )

    child_executor = Executor(
        registry=registry,
        state_storage=storage,
        node_actor=node_actor,
        llm=mock_llm,
        parent_executor=parent_executor,
    )

    assert child_executor.parent_executor == parent_executor
    assert child_executor.is_child is True


def test_executor_init_with_root_output_queue(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    root_queue: Queue[ExecutorOutput] = Queue()
    executor = Executor(
        registry=registry,
        state_storage=storage,
        node_actor=node_actor,
        llm=mock_llm,
        root_output_queue=root_queue,
    )

    assert executor._root_output_queue == root_queue


def test_is_child_true(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    parent_executor = Executor(
        registry=registry,
        state_storage=storage,
        node_actor=node_actor,
        llm=mock_llm,
    )

    child_executor = Executor(
        registry=registry,
        state_storage=storage,
        node_actor=node_actor,
        llm=mock_llm,
        parent_executor=parent_executor,
    )

    assert child_executor.is_child is True


def test_is_child_false(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    executor = Executor(
        registry=registry,
        state_storage=storage,
        node_actor=node_actor,
        llm=mock_llm,
    )

    assert executor.is_child is False


@pytest.mark.asyncio
async def test_step_basic_execution(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    execution_id = uuid4()
    with patch.object(node_actor, "execute", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = Result(output="test result", next_nodes=[])

        executor = Executor(
            registry=registry,
            state_storage=storage,
            node_actor=node_actor,
            llm=mock_llm,
            execution_id=execution_id,
        )

        input_ = ExecutorInput(
            execution_id=execution_id,
            node_actor_id=node_actor.id,
            node_input="test input",
            node_full_name="LLMNode/test",
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
    next_node.full_name = "ToolNode/test"
    next_node_tuple = NextNode(next_node, "next input")

    executor = Executor(
        registry=registry,
        state_storage=storage,
        node_actor=node_actor,
        llm=mock_llm,
        execution_id=execution_id,
    )

    with (
        patch.object(node_actor, "execute", new_callable=AsyncMock) as mock_execute,
        patch.object(executor, "_fork_executor") as mock_fork,
    ):
        input_ = ExecutorInput(
            execution_id=execution_id,
            node_actor_id=node_actor.id,
            node_input="test input",
            node_full_name="LLMNode/test_llm_node",
        )
        mock_execute.side_effect = [
            Result(output="intermediate result", next_nodes=[next_node_tuple]),
            Result(output="final result", next_nodes=[]),
        ]

        # Mock the child executor
        mock_child_executor = Mock()
        mock_child_executor.execution_id = uuid4()
        mock_child_executor.node_actor.id = uuid4()
        mock_child_executor.step = AsyncMock(
            return_value=ExecutorOutput(
                execution_id=mock_child_executor.execution_id,
                node_actor_id=mock_child_executor.node_actor.id,
                node_full_name="ToolNode/test",
                node_output="child result",
                exit_=True,
            )
        )
        mock_fork.return_value = mock_child_executor

        await executor.step(input_)
        mock_fork.assert_called_once_with(next_node)


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
        node_actor=node_actor,
        llm=mock_llm,
        execution_id=execution_id,
        max_iterations=10,
    )

    with (
        patch.object(node_actor, "execute", new_callable=AsyncMock) as mock_execute,
        patch.object(executor, "_fork_executor") as mock_fork,
    ):
        input_ = ExecutorInput(
            execution_id=execution_id,
            node_actor_id=node_actor.id,
            node_input="test input",
            node_full_name=next_node.full_name,
        )
        mock_execute.return_value = Result(
            output="intermediate result", next_nodes=[next_node_tuple]
        )

        # Mock the child executor
        mock_child_executor = Mock()
        mock_child_executor.execution_id = uuid4()
        mock_child_executor.node_actor.id = uuid4()
        mock_child_executor.step = AsyncMock(
            return_value=ExecutorOutput(
                execution_id=mock_child_executor.execution_id,
                node_actor_id=mock_child_executor.node_actor.id,
                node_full_name=next_node.full_name,
                node_output="child result",
                exit_=True,
            )
        )
        mock_fork.return_value = mock_child_executor

        await executor.step(input_)
        assert executor.status == ExecutorStatus.FAILED
        assert executor.iteration_count == 10


@pytest.mark.asyncio
async def test_execute_node_basic(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    execution_id = uuid4()
    executor = Executor(
        registry=registry,
        state_storage=storage,
        node_actor=node_actor,
        llm=mock_llm,
        execution_id=execution_id,
    )
    input_ = ExecutorInput(
        execution_id=execution_id,
        node_actor_id=node_actor.id,
        node_input="test input",
        node_full_name="LLMNode/test_llm_node",
    )

    with (
        patch.object(executor.state_storage, "asave_actor_state") as mock_storage_asave,
        patch.object(
            executor.node_actor, "execute", new_callable=AsyncMock
        ) as mock_execute,
    ):
        mock_execute.return_value = Result(output="test result", next_nodes=[])
        result = await executor._execute_node(input_)

        mock_execute.assert_called_once_with(
            "test input", execution_id=execution_id, context=None
        )
        mock_storage_asave.assert_called_once_with(
            execution_id,
            node_actor.id,
            {
                "actor_id": str(node_actor.id),
                "node_id": str(node_actor.node.id),
                "status": "ready",
                "node_state": {
                    "kind": "LLMNode",
                    "name": "test_llm_node",
                    "context": {},
                    "messages": [],
                    "input_": None,
                    "output": None,
                },
            },
        )
    assert executor.status == ExecutorStatus.RUNNING
    assert result.output == "test result"


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
        node_actor=node_actor,
        llm=mock_llm,
        execution_id=execution_id,
    )

    next_node = Mock(spec=BaseNode)
    next_node.full_name = "next_node/test"

    with patch("liman.executor.base.NodeActor") as mock_node_actor_class:
        mock_child_actor = Mock()
        mock_node_actor_class.create.return_value = mock_child_actor

        child_executor = await executor._fork_executor(next_node)

        assert isinstance(child_executor, Executor)
        assert child_executor.parent_executor == executor
        assert child_executor.node_actor == mock_child_actor
        assert child_executor.execution_id in executor.child_executors
        assert executor.child_executors[child_executor.execution_id] == child_executor

        mock_node_actor_class.create.assert_called_once_with(next_node, llm=mock_llm)


@pytest.mark.asyncio
async def test_handle_parallel_execution(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    execution_id = uuid4()
    executor = Executor(
        registry=registry,
        state_storage=storage,
        node_actor=node_actor,
        llm=mock_llm,
        execution_id=execution_id,
    )

    node1 = Mock(spec=BaseNode)
    node1.full_name = "node1/test"
    node2 = Mock(spec=BaseNode)
    node2.full_name = "node2/test"

    next_nodes: list[NextNode] = [NextNode(node1, "input1"), NextNode(node2, "input2")]

    with patch.object(executor, "_fork_executor") as mock_fork:
        mock_child1 = Mock()
        mock_child1.execution_id = uuid4()
        mock_child1.node_actor.id = uuid4()
        mock_child1.step = AsyncMock(
            return_value=ExecutorOutput(
                execution_id=mock_child1.execution_id,
                node_actor_id=mock_child1.node_actor.id,
                node_full_name="node1/test",
                node_output="result1",
            )
        )

        mock_child2 = Mock()
        mock_child2.execution_id = uuid4()
        mock_child2.node_actor.id = uuid4()
        mock_child2.step = AsyncMock(
            return_value=ExecutorOutput(
                execution_id=mock_child2.execution_id,
                node_actor_id=mock_child2.node_actor.id,
                node_full_name="node2/test",
                node_output="result2",
            )
        )

        mock_fork.side_effect = [mock_child1, mock_child2]

        await executor._handle_parallel_execution(next_nodes)

        assert mock_fork.call_count == 2
        assert executor.status == ExecutorStatus.RUNNING


def test_on_exit_input_loop_cancelled_error(
    registry: Registry,
    storage: InMemoryStateStorage,
    node_actor: NodeActor[LLMNode],
    mock_llm: Mock,
) -> None:
    executor = Executor(
        registry=registry,
        state_storage=storage,
        node_actor=node_actor,
        llm=mock_llm,
    )

    cancelled_task = Mock()
    cancelled_task.result.side_effect = asyncio.CancelledError()

    executor._on_exit_input_loop(cancelled_task)

    assert executor._processing_task is None
