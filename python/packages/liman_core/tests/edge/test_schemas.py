from liman_core.edge.schemas import EdgeSpec


def test_edge_spec_creation() -> None:
    spec = EdgeSpec(target="target_node")

    assert spec.target == "target_node"
    assert spec.when is None
    assert spec.id_ is None
    assert spec.depends is None


def test_edge_spec_with_when() -> None:
    spec = EdgeSpec(target="target_node", when="true")

    assert spec.target == "target_node"
    assert spec.when == "true"


def test_edge_spec_with_id() -> None:
    spec = EdgeSpec(target="target_node", id="edge_1")

    assert spec.target == "target_node"
    assert spec.id_ == "edge_1"


def test_edge_spec_with_depends() -> None:
    depends_list = ["dep1", "dep2"]
    spec = EdgeSpec(target="target_node", depends=depends_list)

    assert spec.target == "target_node"
    assert spec.depends == depends_list


def test_edge_spec_full() -> None:
    spec = EdgeSpec(
        target="target_node",
        when="condition == true",
        id="edge_1",
        depends=["dep1", "dep2"],
    )

    assert spec.target == "target_node"
    assert spec.when == "condition == true"
    assert spec.id_ == "edge_1"
    assert spec.depends == ["dep1", "dep2"]


def test_edge_spec_model_validation() -> None:
    spec_dict = {
        "target": "target_node",
        "when": "true",
        "id": "edge_1",
        "depends": ["dep1"],
    }
    spec = EdgeSpec.model_validate(spec_dict)

    assert spec.target == "target_node"
    assert spec.when == "true"
    assert spec.id_ == "edge_1"
    assert spec.depends == ["dep1"]
