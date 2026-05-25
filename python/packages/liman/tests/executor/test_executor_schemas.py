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
    executor_id = uuid4()
    execution_id = uuid4()
    node_actor_id = uuid4()
    node_input = {"test": "data"}
    node_fullname = "llm_node/test_node"

    input_obj = ExecutorInput(
        executor_id=executor_id,
        execution_id=execution_id,
        node_actor_id=node_actor_id,
        node_input=node_input,
        node_fullname=node_fullname,
    )

    assert input_obj.executor_id == executor_id
    assert input_obj.execution_id == execution_id
    assert input_obj.node_actor_id == node_actor_id
    assert input_obj.node_input == node_input
    assert input_obj.node_fullname == node_fullname


def test_executor_input_with_string_input() -> None:
    input_obj = ExecutorInput(
        executor_id=uuid4(),
        execution_id=uuid4(),
        node_input="test string input",
        node_fullname="llm_node/test_node",
    )

    assert input_obj.node_input == "test string input"


def test_executor_input_with_none_input() -> None:
    input_obj = ExecutorInput(
        executor_id=uuid4(),
        execution_id=uuid4(),
        node_input=None,
        node_fullname="llm_node/test_node",
    )

    assert input_obj.node_input is None


def test_executor_input_validation_error() -> None:
    with pytest.raises(ValidationError):
        ExecutorInput(
            executor_id=uuid4(),
            execution_id="not-a-uuid",
            node_input="test",
            node_fullname="test_node",
        )


def test_create_executor_output_basic() -> None:
    executor_id = uuid4()
    execution_id = uuid4()
    node_actor_id = uuid4()
    node_fullname = "llm_node/test_node"
    node_output = {"result": "success"}

    output_obj = ExecutorOutput(
        executor_id=executor_id,
        execution_id=execution_id,
        node_actor_id=node_actor_id,
        node_fullname=node_fullname,
        node_output=node_output,
    )

    assert output_obj.executor_id == executor_id
    assert output_obj.execution_id == execution_id
    assert output_obj.node_actor_id == node_actor_id
    assert output_obj.node_fullname == node_fullname
    assert output_obj.node_output == node_output
    assert output_obj.exit_ is False
    assert output_obj.error is None
    assert output_obj.error_type is None


def test_create_executor_output_with_exit() -> None:
    output_obj = ExecutorOutput(
        executor_id=uuid4(),
        execution_id=uuid4(),
        node_actor_id=uuid4(),
        node_fullname="llm_node/test_node",
        exit_=True,
    )

    assert output_obj.exit_ is True


def test_create_executor_output_with_error() -> None:
    error_msg = "Something went wrong"
    error_type = "ValueError"

    output_obj = ExecutorOutput(
        executor_id=uuid4(),
        execution_id=uuid4(),
        node_actor_id=uuid4(),
        node_fullname="llm_node/test_node",
        error=error_msg,
        error_type=error_type,
    )

    assert output_obj.error == error_msg
    assert output_obj.error_type == error_type


def test_executor_output_str_with_string_output() -> None:
    output_obj = ExecutorOutput(
        executor_id=uuid4(),
        execution_id=uuid4(),
        node_actor_id=uuid4(),
        node_fullname="llm_node/test_node",
        node_output="Hello, World!",
    )

    assert str(output_obj) == "Hello, World!"


def test_executor_output_str_with_base_message() -> None:
    message = HumanMessage(content="Test message")

    output_obj = ExecutorOutput(
        executor_id=uuid4(),
        execution_id=uuid4(),
        node_actor_id=uuid4(),
        node_fullname="llm_node/test_node",
        node_output=message,
    )

    assert str(output_obj) == "Test message"


def test_executor_output_str_with_base_message_list_content() -> None:
    message = HumanMessage(content=["Part 1", "Part 2", "Part 3"])

    output_obj = ExecutorOutput(
        executor_id=uuid4(),
        execution_id=uuid4(),
        node_actor_id=uuid4(),
        node_fullname="llm_node/test_node",
        node_output=message,
    )

    assert str(output_obj) == "Part 1\nPart 2\nPart 3"


def test_executor_output_str_with_other_types() -> None:
    node_output = {"key": "value", "number": 42}

    output_obj = ExecutorOutput(
        executor_id=uuid4(),
        execution_id=uuid4(),
        node_actor_id=uuid4(),
        node_fullname="llm_node/test_node",
        node_output=node_output,
    )

    assert str(output_obj) == "{'key': 'value', 'number': 42}"


def test_executor_output_str_with_none_output() -> None:
    output_obj = ExecutorOutput(
        executor_id=uuid4(),
        execution_id=uuid4(),
        node_actor_id=uuid4(),
        node_fullname="llm_node/test_node",
        node_output=None,
    )

    assert str(output_obj) == "None"


def test_executor_output_validation_error() -> None:
    with pytest.raises(ValidationError):
        ExecutorOutput(
            executor_id=uuid4(),
            execution_id="not-a-uuid",
            node_actor_id=uuid4(),
            node_fullname="test_node",
        )


def test_create_executor_state_basic() -> None:
    executor_id = uuid4()
    node_actor_id = uuid4()
    status = ExecutorStatus.RUNNING

    state_obj = ExecutorState(
        executor_id=executor_id,
        node_actor_id=node_actor_id,
        iteration_count=0,
        status=status,
        child_executor_ids=set(),
    )

    assert state_obj.executor_id == executor_id
    assert state_obj.node_actor_id == node_actor_id
    assert state_obj.status == status
    assert state_obj.child_executor_ids == set()


def test_create_executor_state_with_children() -> None:
    child_ids = {uuid4(), uuid4(), uuid4()}

    state_obj = ExecutorState(
        executor_id=uuid4(),
        node_actor_id=uuid4(),
        iteration_count=0,
        status=ExecutorStatus.SUSPENDED,
        child_executor_ids=child_ids,
    )

    assert state_obj.child_executor_ids == child_ids


def test_executor_state_empty_children_default() -> None:
    state_obj = ExecutorState(
        executor_id=uuid4(),
        node_actor_id=uuid4(),
        iteration_count=0,
        status=ExecutorStatus.IDLE,
        child_executor_ids=set(),
    )

    assert isinstance(state_obj.child_executor_ids, set)
    assert len(state_obj.child_executor_ids) == 0


def test_executor_state_with_all_statuses() -> None:
    node_actor_id = uuid4()

    for status in ExecutorStatus:
        state_obj = ExecutorState(
            executor_id=uuid4(),
            node_actor_id=node_actor_id,
            iteration_count=0,
            status=status,
            child_executor_ids=set(),
        )
        assert state_obj.status == status


def test_executor_state_validation_error() -> None:
    with pytest.raises(ValidationError):
        ExecutorState(
            executor_id="not-a-uuid",
            node_actor_id=uuid4(),
            iteration_count=0,
            status=ExecutorStatus.RUNNING,
            child_executor_ids=set(),
        )
