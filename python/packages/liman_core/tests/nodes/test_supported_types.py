import pytest

from liman_core.nodes.function_node import FunctionNode
from liman_core.nodes.llm_node import LLMNode
from liman_core.nodes.supported_types import get_node_cls
from liman_core.nodes.tool_node import ToolNode


def test_get_node_cls_llm_node() -> None:
    node_cls = get_node_cls("LLMNode")

    assert node_cls == LLMNode


def test_get_node_cls_tool_node() -> None:
    node_cls = get_node_cls("ToolNode")

    assert node_cls == ToolNode


def test_get_node_cls_function_node() -> None:
    node_cls = get_node_cls("FunctionNode")

    assert node_cls == FunctionNode


def test_get_node_cls_unsupported_type() -> None:
    with pytest.raises(ValueError) as exc_info:
        get_node_cls("UnsupportedNode")

    assert "Unsupported node type: UnsupportedNode" in str(exc_info.value)


def test_get_node_cls_case_sensitive() -> None:
    with pytest.raises(ValueError) as exc_info:
        get_node_cls("llmnode")

    assert "Unsupported node type: llmnode" in str(exc_info.value)


def test_get_node_cls_empty_string() -> None:
    with pytest.raises(ValueError) as exc_info:
        get_node_cls("")

    assert "Unsupported node type: " in str(exc_info.value)
