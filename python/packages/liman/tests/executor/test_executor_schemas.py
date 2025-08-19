from uuid import uuid4

import pytest
from langchain_core.messages import HumanMessage
from pydantic import ValidationError

from liman.executor.schemas import (
    ExecutorInput,
    ExecutorOutput,
    ExecutorState,
    ExecutorStatus,
)


def test_create_executor_input() -> None:
    execution_id = uuid4()
    node_actor_id = uuid4()
    node_input = {"test": "data"}
    node_full_name = "llm_node/test_node"

    input_obj = ExecutorInput(
        execution_id=execution_id,
        node_actor_id=node_actor_id,
        node_input=node_input,
        node_full_name=node_full_name,
    )

    assert input_obj.execution_id == execution_id
    assert input_obj.node_actor_id == node_actor_id
    assert input_obj.node_input == node_input
    assert input_obj.node_full_name == node_full_name


def test_executor_input_with_string_input() -> None:
    execution_id = uuid4()
    node_actor_id = uuid4()
    node_input = "test string input"
    node_full_name = "llm_node/test_node"

    input_obj = ExecutorInput(
        execution_id=execution_id,
        node_actor_id=node_actor_id,
        node_input=node_input,
        node_full_name=node_full_name,
    )

    assert input_obj.node_input == node_input


def test_executor_input_with_none_input() -> None:
    execution_id = uuid4()
    node_actor_id = uuid4()
    node_input = None
    node_full_name = "llm_node/test_node"

    input_obj = ExecutorInput(
        execution_id=execution_id,
        node_actor_id=node_actor_id,
        node_input=node_input,
        node_full_name=node_full_name,
    )

    assert input_obj.node_input is None


def test_executor_input_validation_error() -> None:
    with pytest.raises(ValidationError):
        ExecutorInput(
            execution_id="not-a-uuid",
            node_actor_id=uuid4(),
            node_input="test",
            node_full_name="test_node",
        )


def test_create_executor_output_basic() -> None:
    execution_id = uuid4()
    node_actor_id = uuid4()
    node_full_name = "llm_node/test_node"
    node_output = {"result": "success"}

    output_obj = ExecutorOutput(
        execution_id=execution_id,
        node_actor_id=node_actor_id,
        node_full_name=node_full_name,
        node_output=node_output,
    )

    assert output_obj.execution_id == execution_id
    assert output_obj.node_actor_id == node_actor_id
    assert output_obj.node_full_name == node_full_name
    assert output_obj.node_output == node_output
    assert output_obj.exit_ is False
    assert output_obj.error is None
    assert output_obj.error_type is None


def test_create_executor_output_with_exit() -> None:
    execution_id = uuid4()
    node_actor_id = uuid4()
    node_full_name = "llm_node/test_node"

    output_obj = ExecutorOutput(
        execution_id=execution_id,
        node_actor_id=node_actor_id,
        node_full_name=node_full_name,
        exit_=True,
    )

    assert output_obj.exit_ is True


def test_create_executor_output_with_error() -> None:
    execution_id = uuid4()
    node_actor_id = uuid4()
    node_full_name = "llm_node/test_node"
    error_msg = "Something went wrong"
    error_type = "ValueError"

    output_obj = ExecutorOutput(
        execution_id=execution_id,
        node_actor_id=node_actor_id,
        node_full_name=node_full_name,
        error=error_msg,
        error_type=error_type,
    )

    assert output_obj.error == error_msg
    assert output_obj.error_type == error_type


def test_executor_output_str_with_string_output() -> None:
    execution_id = uuid4()
    node_actor_id = uuid4()
    node_full_name = "llm_node/test_node"
    node_output = "Hello, World!"

    output_obj = ExecutorOutput(
        execution_id=execution_id,
        node_actor_id=node_actor_id,
        node_full_name=node_full_name,
        node_output=node_output,
    )

    assert str(output_obj) == "Hello, World!"


def test_executor_output_str_with_base_message() -> None:
    execution_id = uuid4()
    node_actor_id = uuid4()
    node_full_name = "llm_node/test_node"
    message = HumanMessage(content="Test message")

    output_obj = ExecutorOutput(
        execution_id=execution_id,
        node_actor_id=node_actor_id,
        node_full_name=node_full_name,
        node_output=message,
    )

    assert str(output_obj) == "Test message"


def test_executor_output_str_with_base_message_list_content() -> None:
    execution_id = uuid4()
    node_actor_id = uuid4()
    node_full_name = "llm_node/test_node"
    message = HumanMessage(content=["Part 1", "Part 2", "Part 3"])

    output_obj = ExecutorOutput(
        execution_id=execution_id,
        node_actor_id=node_actor_id,
        node_full_name=node_full_name,
        node_output=message,
    )

    assert str(output_obj) == "Part 1\nPart 2\nPart 3"


def test_executor_output_str_with_other_types() -> None:
    execution_id = uuid4()
    node_actor_id = uuid4()
    node_full_name = "llm_node/test_node"
    node_output = {"key": "value", "number": 42}

    output_obj = ExecutorOutput(
        execution_id=execution_id,
        node_actor_id=node_actor_id,
        node_full_name=node_full_name,
        node_output=node_output,
    )

    assert str(output_obj) == "{'key': 'value', 'number': 42}"


def test_executor_output_str_with_none_output() -> None:
    execution_id = uuid4()
    node_actor_id = uuid4()
    node_full_name = "llm_node/test_node"

    output_obj = ExecutorOutput(
        execution_id=execution_id,
        node_actor_id=node_actor_id,
        node_full_name=node_full_name,
        node_output=None,
    )

    assert str(output_obj) == "None"


def test_executor_output_validation_error() -> None:
    with pytest.raises(ValidationError):
        ExecutorOutput(
            execution_id="not-a-uuid",
            node_actor_id=uuid4(),
            node_full_name="test_node",
        )


def test_create_executor_state_basic() -> None:
    execution_id = uuid4()
    node_actor_id = uuid4()
    status = ExecutorStatus.RUNNING

    state_obj = ExecutorState(
        execution_id=execution_id, node_actor_id=node_actor_id, status=status
    )

    assert state_obj.execution_id == execution_id
    assert state_obj.node_actor_id == node_actor_id
    assert state_obj.status == status
    assert state_obj.child_executor_ids == set()


def test_create_executor_state_with_children() -> None:
    execution_id = uuid4()
    node_actor_id = uuid4()
    status = ExecutorStatus.SUSPENDED
    child_ids = {uuid4(), uuid4(), uuid4()}

    state_obj = ExecutorState(
        execution_id=execution_id,
        node_actor_id=node_actor_id,
        status=status,
        child_executor_ids=child_ids,
    )

    assert state_obj.child_executor_ids == child_ids


def test_executor_state_empty_children_default() -> None:
    execution_id = uuid4()
    node_actor_id = uuid4()
    status = ExecutorStatus.IDLE

    state_obj = ExecutorState(
        execution_id=execution_id, node_actor_id=node_actor_id, status=status
    )

    assert isinstance(state_obj.child_executor_ids, set)
    assert len(state_obj.child_executor_ids) == 0


def test_executor_state_with_all_statuses() -> None:
    execution_id = uuid4()
    node_actor_id = uuid4()

    for status in ExecutorStatus:
        state_obj = ExecutorState(
            execution_id=execution_id, node_actor_id=node_actor_id, status=status
        )
        assert state_obj.status == status


def test_executor_state_validation_error() -> None:
    with pytest.raises(ValidationError):
        ExecutorState(
            execution_id="not-a-uuid",
            node_actor_id=uuid4(),
            status=ExecutorStatus.RUNNING,
        )
