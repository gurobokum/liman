from langchain_core.messages import HumanMessage

from liman_core.edge.schemas import EdgeSpec
from liman_core.nodes.function_node.schemas import FunctionNodeSpec, FunctionNodeState


def test_function_node_spec_creation() -> None:
    spec = FunctionNodeSpec(name="test_function")

    assert spec.name == "test_function"
    assert spec.kind == "FunctionNode"
    assert spec.func is None
    assert spec.description is None
    assert spec.prompts is None
    assert spec.nodes == []
    assert spec.llm_nodes == []
    assert spec.tools == []


def test_function_node_spec_with_func() -> None:
    spec = FunctionNodeSpec(name="test_function", func="my_func")

    assert spec.name == "test_function"
    assert spec.func == "my_func"


def test_function_node_spec_with_edges() -> None:
    edge1 = EdgeSpec(target="target1")
    edge2 = EdgeSpec(target="target2")
    spec = FunctionNodeSpec(
        name="test_function",
        nodes=["node1", edge1],
        llm_nodes=["llm1", edge2],
        tools=["tool1", "tool2"],
    )

    assert spec.nodes == ["node1", edge1]
    assert spec.llm_nodes == ["llm1", edge2]
    assert spec.tools == ["tool1", "tool2"]


def test_function_node_spec_model_validation() -> None:
    spec_dict = {"name": "test_function", "func": "my_func", "tools": ["tool1"]}
    spec = FunctionNodeSpec.model_validate(spec_dict)

    assert spec.name == "test_function"
    assert spec.func == "my_func"
    assert spec.tools == ["tool1"]


def test_function_node_state_creation() -> None:
    state = FunctionNodeState(name="test_function")

    assert state.name == "test_function"
    assert state.kind == "FunctionNode"
    assert state.messages == []
    assert state.input_ is None
    assert state.output is None


def test_function_node_state_with_data() -> None:
    message = HumanMessage(content="Hello")
    state = FunctionNodeState(
        name="test_function",
        messages=[message],
        input_={"key": "value"},
        output="result",
    )

    assert state.name == "test_function"
    assert state.messages == [message]
    assert state.input_ == {"key": "value"}
    assert state.output == "result"


def test_function_node_state_model_validation() -> None:
    state_dict = {
        "name": "test_function",
        "input_": {"data": "test"},
        "output": "processed",
    }
    state = FunctionNodeState.model_validate(state_dict)

    assert state.name == "test_function"
    assert state.input_ == {"data": "test"}
    assert state.output == "processed"
