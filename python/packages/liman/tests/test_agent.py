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

from liman.agent import Agent, NodeAgentConfig
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
    mock_executor.execution_id = uuid4()
    mock_executor.node_actor = node_actor
    mock_executor.step = AsyncMock(
        return_value=ExecutorOutput(
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
        assert agent._executor is None
        assert agent._last_node_actor_cfg is None


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
        agent, "_create_executor", return_value=executor
    ) as mock_executor:
        output = await agent.step("Hello")

        mock_executor.assert_called_once_with("Hello")
        assert output.node_output == "Hello, World!"
        assert output.exit_ is True


@pytest.mark.parametrize(
    "executor", [{"node_output": "Response", "exit_": True}], indirect=True
)
@pytest.mark.asyncio
async def test_step_with_executor_input(agent: Agent, executor: Executor) -> None:
    executor_input = ExecutorInput(
        execution_id=executor.execution_id,
        node_actor_id=executor.node_actor.id,
        node_input="Test input",
        node_full_name=executor.node_actor.node.full_name,
    )

    with patch.object(agent, "_create_executor", return_value=executor) as mock_create:
        output = await agent.step(executor_input)

        mock_create.assert_called_once_with(executor_input)
        assert output.node_output == "Response"


@pytest.mark.parametrize("executor", [{"node_output": "First response"}], indirect=True)
@pytest.mark.asyncio
async def test_step_subsequent_calls_with_string(
    agent: Agent, executor: Executor
) -> None:
    agent._executor = executor
    agent._last_node_actor_cfg = {
        "execution_id": executor.execution_id,
        "node_actor_id": executor.node_actor.id,
        "node_full_name": "LLMNode/start",
    }

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
        patch.object(agent, "_create_executor", return_value=executor),
        pytest.raises(RuntimeError, match="exceeded max iterations"),
    ):
        await agent.step("First")


@pytest.mark.asyncio
async def test_create_executor_with_string_input(
    agent: Agent, node_actor: NodeActor[Any], registry: Registry
) -> None:
    with (
        patch.object(agent, "_create_initial_node_actor") as mock_create_actor,
        patch.object(registry, "lookup") as mock_lookup,
    ):
        mock_create_actor.return_value = node_actor
        mock_lookup.return_value = node_actor.node

        result = await agent._create_executor("Hello")

        assert isinstance(result, Executor)
        assert result.node_actor == node_actor
        assert result.registry == agent.registry


@pytest.mark.asyncio
async def test_create_executor_with_full_node_name(
    agent: Agent, node_actor: NodeActor[Any], registry: Registry
) -> None:
    with (
        patch.object(agent, "_create_initial_node_actor") as mock_create_actor,
        patch.object(registry, "lookup") as mock_lookup,
    ):
        mock_lookup.return_value = node_actor.node
        mock_create_actor.return_value = node_actor
        node_actor.node.full_name = "LLMNode/start"

        result = await agent._create_executor("Hello")

        assert isinstance(result, Executor)
        mock_lookup.assert_called_once()


@pytest.mark.asyncio
async def test_create_executor_with_executor_input(
    agent: Agent, node_actor: NodeActor[Any]
) -> None:
    execution_id = uuid4()
    executor_input = ExecutorInput(
        execution_id=execution_id,
        node_actor_id=node_actor.id,
        node_input="Test",
        node_full_name="LLMNode/start",
    )

    with patch.object(agent, "_create_initial_node_actor") as mock_create_actor:
        mock_create_actor.return_value = node_actor

        result = await agent._create_executor(executor_input)

        assert result.execution_id == execution_id
        mock_create_actor.assert_called_once_with(executor_input, execution_id)


@pytest.mark.parametrize("executor", [{"node_output": "test"}], indirect=True)
def test_get_node_actor_cfg(agent: Agent, executor: Executor) -> None:
    output = ExecutorOutput(
        execution_id=executor.execution_id,
        node_actor_id=executor.node_actor.id,
        node_full_name=executor.node_actor.node.full_name,
        node_output="test",
    )

    result = agent._get_node_actor_cfg(output)

    expected: NodeAgentConfig = {
        "execution_id": executor.execution_id,
        "node_actor_id": executor.node_actor.id,
        "node_full_name": executor.node_actor.node.full_name,
    }
    assert result == expected


@pytest.mark.parametrize("executor", [{"node_output": "test input"}], indirect=True)
def test_create_executor_input_with_last_cfg(agent: Agent, executor: Executor) -> None:
    agent._last_node_actor_cfg = {
        "execution_id": executor.execution_id,
        "node_actor_id": executor.node_actor.id,
        "node_full_name": executor.node_actor.node.full_name,
    }

    result = agent._create_executor_input("test input")

    assert result.execution_id == executor.execution_id
    assert result.node_actor_id == executor.node_actor.id
    assert result.node_full_name == executor.node_actor.node.full_name
    assert result.node_input == "test input"


@pytest.mark.parametrize("executor", [{"node_output": "test input"}], indirect=True)
def test_create_executor_input_without_last_cfg(
    agent: Agent, executor: Executor
) -> None:
    agent._executor = executor
    agent._last_node_actor_cfg = None

    result = agent._create_executor_input("test input")

    assert result.execution_id == executor.execution_id
    assert result.node_actor_id == executor.node_actor.id
    assert result.node_full_name == executor.node_actor.node.full_name
    assert result.node_input == "test input"


def test_create_executor_input_without_executor_raises_error(agent: Agent) -> None:
    agent._executor = None
    agent._last_node_actor_cfg = None

    with pytest.raises(RuntimeError, match="Executor is not created yet"):
        agent._create_executor_input("test input")


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
