from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from liman_core.nodes.base.schemas import LangChainMessage, NodeState


def test_node_state_creation() -> None:
    state = NodeState(kind="TestKind", name="test_name")

    assert state.kind == "TestKind"
    assert state.name == "test_name"
    assert state.context == {}


def test_node_state_with_context() -> None:
    context_data = {"key1": "value1", "key2": 42}
    state = NodeState(kind="TestKind", name="test_name", context=context_data)

    assert state.kind == "TestKind"
    assert state.name == "test_name"
    assert state.context == context_data


def test_node_state_model_validation() -> None:
    state_dict = {"kind": "TestKind", "name": "test_name", "context": {"test": "data"}}
    state = NodeState.model_validate(state_dict)

    assert state.kind == "TestKind"
    assert state.name == "test_name"
    assert state.context == {"test": "data"}


def test_langchain_message_types() -> None:
    ai_msg = AIMessage(content="AI response")
    human_msg = HumanMessage(content="Human input")
    tool_msg = ToolMessage(content="Tool result", tool_call_id="123")

    assert isinstance(ai_msg, LangChainMessage)
    assert isinstance(human_msg, LangChainMessage)
    assert isinstance(tool_msg, LangChainMessage)
