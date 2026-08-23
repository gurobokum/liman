from typing import Any

import pytest
from pydantic import ValidationError

from liman_core.edge.schemas import EdgeSpec
from liman_core.nodes.function_node.schemas import FunctionNodeSpec
from liman_core.nodes.llm_node.schemas import LLMNodeSpec
from liman_core.nodes.node.schemas import NodeSpec
from liman_core.nodes.tool_node.schemas import ToolNodeSpec

LLM_NODE_DICT: dict[str, Any] = {
    "kind": "LLMNode",
    "name": "test_node",
    "prompts": {"system": {"en": "test"}},
}


def test_to_accepts_string_and_object_entries() -> None:
    spec = NodeSpec(
        name="test_node",
        func="module.func",
        to=["LLMNode/a", EdgeSpec(ref="Node/b", when="true")],
    )

    assert spec.to == ["LLMNode/a", EdgeSpec(ref="Node/b", when="true")]


def test_to_object_entry_from_dict() -> None:
    spec = NodeSpec.model_validate(
        {
            "kind": "Node",
            "name": "test_node",
            "func": "module.func",
            "to": [{"ref": "LLMNode/a", "when": "status == 'done'"}],
        }
    )

    assert spec.to == [EdgeSpec(ref="LLMNode/a", when="status == 'done'")]


@pytest.mark.parametrize("field", ["nodes", "llm_nodes"])
def test_node_spec_rejects_to_with_legacy_field(field: str) -> None:
    with pytest.raises(ValidationError, match="Cannot mix 'to'"):
        NodeSpec.model_validate(
            {
                "kind": "Node",
                "name": "test_node",
                "func": "module.func",
                "to": ["LLMNode/a"],
                field: ["x"],
            }
        )


@pytest.mark.parametrize("field", ["nodes", "llm_nodes"])
def test_function_node_spec_rejects_to_with_legacy_field(field: str) -> None:
    with pytest.raises(ValidationError, match="Cannot mix 'to'"):
        FunctionNodeSpec.model_validate(
            {
                "kind": "FunctionNode",
                "name": "test_node",
                "to": ["LLMNode/a"],
                field: ["x"],
            }
        )


def test_llm_node_spec_rejects_to_with_legacy_field() -> None:
    with pytest.raises(ValidationError, match="Cannot mix 'to'"):
        LLMNodeSpec.model_validate({**LLM_NODE_DICT, "to": ["Node/a"], "nodes": ["x"]})


def test_tool_node_spec_rejects_to_with_legacy_field() -> None:
    with pytest.raises(ValidationError, match="Cannot mix 'to'"):
        ToolNodeSpec.model_validate(
            {
                "kind": "ToolNode",
                "name": "test_node",
                "to": ["LLMNode/a"],
                "llm_nodes": [{"ref": "LLMNode/x"}],
            }
        )


def test_to_alone_is_valid() -> None:
    spec = LLMNodeSpec.model_validate({**LLM_NODE_DICT, "to": ["Node/a"]})

    assert spec.to == ["Node/a"]
    assert spec.nodes == []


def test_legacy_fields_alone_are_valid() -> None:
    spec = FunctionNodeSpec.model_validate(
        {
            "kind": "FunctionNode",
            "name": "test_node",
            "nodes": ["a", {"ref": "Node/b"}],
            "llm_nodes": ["c"],
        }
    )

    assert spec.to == []
    assert spec.nodes == ["a", EdgeSpec(ref="Node/b")]
