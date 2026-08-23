import pytest
from pydantic import ValidationError

from liman_core.edge.schemas import EdgeSpec


def test_edge_spec_creation() -> None:
    spec = EdgeSpec(ref="LLMNode/target_node")

    assert spec.ref == "LLMNode/target_node"
    assert spec.kind == "LLMNode"
    assert spec.name == "target_node"
    assert spec.when is None


def test_edge_spec_with_when() -> None:
    spec = EdgeSpec(ref="Node/target_node", when="true")

    assert spec.kind == "Node"
    assert spec.name == "target_node"
    assert spec.when == "true"


def test_edge_spec_custom_kind() -> None:
    spec = EdgeSpec(ref="MyPluginNode/target_node")

    assert spec.kind == "MyPluginNode"
    assert spec.name == "target_node"


def test_edge_spec_rejects_tool_node_target() -> None:
    with pytest.raises(ValidationError, match="use the 'tools' field"):
        EdgeSpec(ref="ToolNode/target_node")


@pytest.mark.parametrize("ref", ["bare_name", "a/b/c", "/x", "x/", ""])
def test_edge_spec_invalid_ref(ref: str) -> None:
    with pytest.raises(ValidationError):
        EdgeSpec(ref=ref)


def test_edge_spec_model_validation() -> None:
    spec_dict = {
        "ref": "Node/target_node",
        "when": "true",
    }
    spec = EdgeSpec.model_validate(spec_dict)

    assert spec.ref == "Node/target_node"
    assert spec.when == "true"
