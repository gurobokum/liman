import asyncio
from collections.abc import Generator
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from liman_core.node_actor.actor import NodeActor
from liman_core.registry import Registry

from liman.agent import Agent
from liman.executor.base import Executor
from liman.executor.schemas import ExecutorInput, ExecutorOutput
from liman.state import InMemoryStateStorage


@pytest.fixture
def mock_llm() -> Mock:
    return Mock(spec=BaseChatModel)


@pytest.fixture
def agent(
    mock_llm: Mock,
    registry: Registry,
    storage: InMemoryStateStorage,
    request: pytest.FixtureRequest,
) -> Generator[Agent, None, None]:
    params = getattr(request, "param", {})
    start_node = params.get("start_node", "LLMNode/start")
    max_iterations = params.get("max_iterations", 50)

    with (
        TemporaryDirectory() as temp_dir,
        patch("liman.agent.load_specs_from_directory"),
    ):
        yield Agent(
            specs_dir=temp_dir,
            start_node=start_node,
            llm=mock_llm,
            registry=registry,
            state_storage=storage,
            max_iterations=max_iterations,
        )


@pytest.fixture
def node_actor(request: pytest.FixtureRequest) -> NodeActor[Any]:
    node_full_name = getattr(request, "param", "LLMNode/start")

    mock_actor = Mock(spec=NodeActor)
    mock_actor.node = Mock()
    mock_actor.node.full_name = node_full_name
    mock_actor.id = uuid4()
    return mock_actor


@pytest.fixture
def executor(node_actor: NodeActor[Any], request: pytest.FixtureRequest) -> Executor:
    param = getattr(request, "param", {})
    node_output = param["node_output"]
    exit_ = param.get("exit_", True)

    mock_executor = Mock(spec=Executor)
    mock_executor.id = uuid4()
    mock_executor.execution_id = uuid4()
    mock_executor.node_actor = node_actor
    mock_executor.step = AsyncMock(
        return_value=ExecutorOutput(
            executor_id=mock_executor.id,
            execution_id=mock_executor.execution_id,
            node_actor_id=node_actor.id,
            node_full_name=node_actor.node.full_name,
            node_output=node_output,
            exit_=exit_,
        )
    )
    return mock_executor


def test_agent_init_basic(mock_llm: Mock) -> None:
    with TemporaryDirectory() as temp_dir:
        agent = Agent(specs_dir=temp_dir, start_node="start", llm=mock_llm)

        assert isinstance(agent.id, UUID)
        assert agent.specs_dir == temp_dir
        assert agent.start_node == "start"
        assert agent.llm == mock_llm
        assert agent.name == "Agent"
        assert isinstance(agent.registry, Registry)
        assert isinstance(agent.state_storage, InMemoryStateStorage)
        assert agent.max_iterations == 50
        assert agent.iteration_count == 0
        assert agent._root_executor is None


@pytest.mark.parametrize(
    "agent", [{"start_node": "custom_start", "max_iterations": 100}], indirect=True
)
def test_agent_init_with_custom_params(
    agent: Agent, registry: Registry, storage: InMemoryStateStorage
) -> None:
    assert agent.name == "Agent"
    assert agent.start_node == "custom_start"
    assert agent.registry == registry
    assert agent.state_storage == storage
    assert agent.max_iterations == 100


@patch("liman.agent.load_specs_from_directory")
def test_agent_init_loads_specs(mock_load_specs: Mock, mock_llm: Mock) -> None:
    with TemporaryDirectory() as temp_dir:
        agent = Agent(specs_dir=temp_dir, start_node="start", llm=mock_llm)

        mock_load_specs.assert_called_once_with(temp_dir, agent.registry)


@pytest.mark.parametrize(
    "executor", [{"node_output": "Hello, World!", "exit_": True}], indirect=True
)
@pytest.mark.asyncio
async def test_step_with_string_input_first_time(
    agent: Agent, executor: Executor
) -> None:
    with patch.object(
        agent, "_get_or_create_executor", new=AsyncMock(return_value=executor)
    ):
        output = await agent.step("Hello")

        assert output.node_output == "Hello, World!"
        assert output.exit_ is True


@pytest.mark.parametrize(
    "executor", [{"node_output": "Response", "exit_": True}], indirect=True
)
@pytest.mark.asyncio
async def test_step_with_executor_input(
    agent: Agent, executor: Executor, node_actor: NodeActor[Any]
) -> None:
    executor_input = ExecutorInput(
        executor_id=executor.id,
        execution_id=executor.execution_id,
        node_actor_id=node_actor.id,
        node_input="Test input",
        node_fullname=node_actor.node.full_name,
    )

    with patch.object(
        agent, "_get_or_create_executor", new=AsyncMock(return_value=executor)
    ):
        output = await agent.step(executor_input)

        assert output.node_output == "Response"


@pytest.mark.parametrize("executor", [{"node_output": "First response"}], indirect=True)
@pytest.mark.asyncio
async def test_step_subsequent_calls_with_string(
    agent: Agent, executor: Executor
) -> None:
    agent._root_executor = executor
    agent._executors[executor.execution_id] = executor

    output = await agent.step("Follow-up")

    assert output.node_output == "First response"
    executor.step.assert_called_once()  # type: ignore[attr-defined]
    call_args = executor.step.call_args[0][0]  # type: ignore[attr-defined]
    assert call_args.node_input == "Follow-up"
    assert call_args.execution_id == executor.execution_id


@pytest.mark.skip("Skipping test for max iterations exceeded until implemented")
@pytest.mark.parametrize("agent", [{"max_iterations": 1}], indirect=True)
@pytest.mark.parametrize(
    "executor", [{"node_output": "Response", "exit_": False}], indirect=True
)
@pytest.mark.asyncio
async def test_step_max_iterations_exceeded(agent: Agent, executor: Executor) -> None:
    with (
        patch.object(
            agent, "_get_or_create_executor", new=AsyncMock(return_value=executor)
        ),
        pytest.raises(RuntimeError, match="exceeded max iterations"),
    ):
        await agent.step("First")


@pytest.mark.asyncio
async def test_get_or_create_executor_with_string_input(agent: Agent) -> None:
    result = await agent._get_or_create_executor("Hello")

    assert isinstance(result, Executor)
    assert result.registry == agent.registry
    assert agent._root_executor is result


@pytest.mark.parametrize("executor", [{"node_output": "test"}], indirect=True)
@pytest.mark.asyncio
async def test_get_or_create_executor_with_executor_input_found(
    agent: Agent, executor: Executor
) -> None:
    agent._executors[executor.execution_id] = executor
    executor_input = ExecutorInput(
        executor_id=executor.id,
        execution_id=executor.execution_id,
        node_input="Test",
        node_fullname="LLMNode/start",
    )

    result = await agent._get_or_create_executor(executor_input)

    assert result is executor


@pytest.mark.parametrize("executor", [{"node_output": "test input"}], indirect=True)
@pytest.mark.asyncio
async def test_create_executor_input_with_root_executor(
    agent: Agent, executor: Executor
) -> None:
    agent._root_executor = executor

    result = await agent._create_executor_input("test input")

    assert result.executor_id == executor.id
    assert result.execution_id == executor.execution_id
    assert result.node_input == "test input"
    assert result.node_fullname == agent.start_node


@pytest.mark.asyncio
async def test_create_executor_input_without_root_executor(agent: Agent) -> None:
    assert agent._root_executor is None

    result = await agent._create_executor_input("test input")

    assert result.node_input == "test input"
    assert result.node_fullname == agent.start_node
    assert agent._root_executor is not None
    assert result.executor_id == agent._root_executor.id


def test_on_exit_input_loop_cancelled_error(agent: Agent) -> None:
    cancelled_task = Mock()
    cancelled_task.result.side_effect = asyncio.CancelledError()

    agent._on_exit_input_loop(cancelled_task)

    assert agent._processing_task is None


def test_on_exit_input_loop_other_exception(agent: Agent) -> None:
    failed_task = Mock()
    failed_task.result.side_effect = RuntimeError("Task failed")

    with pytest.raises(RuntimeError, match="Task failed"):
        agent._on_exit_input_loop(failed_task)
