from typing import Any

import pytest

from liman_core.base.schemas import BaseSpec
from liman_core.errors import LimanError
from liman_core.nodes.base.node import BaseNode
from liman_core.nodes.base.schemas import NodeState
from liman_core.registry import Registry


class MockNodeSpec(BaseSpec):
    kind: str = "TestNode"
    name: str


class MockNodeState(NodeState):
    test_value: str = "default"


class MockNode(BaseNode[MockNodeSpec, MockNodeState]):
    spec_type = MockNodeSpec

    def compile(self) -> None:
        self._compiled = True

    async def invoke(self, *args: Any, **kwargs: Any) -> Any:
        return "invoked"

    def get_new_state(self) -> MockNodeState:
        return MockNodeState(kind=self.spec.kind, name=self.name)


def test_base_node_creation(registry: Registry) -> None:
    spec = MockNodeSpec(kind="TestNode", name="test_node")
    node = MockNode(spec, registry)

    assert node.spec == spec
    assert node.name == "test_node"
    assert node.default_lang == "en"
    assert node.fallback_lang == "en"
    assert not node._compiled


def test_base_node_with_custom_languages(registry: Registry) -> None:
    spec = MockNodeSpec(kind="TestNode", name="test_node")
    node = MockNode(spec, registry, default_lang="ru", fallback_lang="fr")

    assert node.default_lang == "ru"
    assert node.fallback_lang == "fr"


def test_base_node_invalid_default_language(registry: Registry) -> None:
    spec = MockNodeSpec(kind="TestNode", name="test_node")

    with pytest.raises(LimanError) as exc_info:
        MockNode(spec, registry, default_lang="invalid")

    assert "Invalid default language code: invalid" in str(exc_info.value)


def test_base_node_invalid_fallback_language(registry: Registry) -> None:
    spec = MockNodeSpec(kind="TestNode", name="test_node")

    with pytest.raises(LimanError) as exc_info:
        MockNode(spec, registry, fallback_lang="invalid")

    assert "Invalid fallback language code: invalid" in str(exc_info.value)


def test_base_node_repr(registry: Registry) -> None:
    spec = MockNodeSpec(kind="TestNode", name="test_node")
    node = MockNode(spec, registry)

    assert repr(node) == "TestNode:test_node"


def test_base_node_is_llm_node(registry: Registry) -> None:
    spec = MockNodeSpec(kind="LLMNode", name="test_node")
    node = MockNode(spec, registry)

    assert node.is_llm_node is True
    assert node.is_tool_node is False


def test_base_node_is_tool_node(registry: Registry) -> None:
    spec = MockNodeSpec(kind="ToolNode", name="test_node")
    node = MockNode(spec, registry)

    assert node.is_tool_node is True
    assert node.is_llm_node is False


def test_base_node_compile(registry: Registry) -> None:
    spec = MockNodeSpec(kind="TestNode", name="test_node")
    node = MockNode(spec, registry)

    assert not node._compiled
    node.compile()
    assert node._compiled


@pytest.mark.asyncio
async def test_base_node_invoke(registry: Registry) -> None:
    spec = MockNodeSpec(kind="TestNode", name="test_node")
    node = MockNode(spec, registry)

    result = await node.invoke()

    assert result == "invoked"


def test_base_node_get_new_state(registry: Registry) -> None:
    spec = MockNodeSpec(kind="TestNode", name="test_node")
    node = MockNode(spec, registry)

    state = node.get_new_state()

    assert isinstance(state, MockNodeState)
    assert state.kind == "TestNode"
    assert state.name == "test_node"
    assert state.test_value == "default"


def test_base_node_generate_id(registry: Registry) -> None:
    spec = MockNodeSpec(kind="TestNode", name="test_node")
    node = MockNode(spec, registry)

    id1 = node.generate_id()
    id2 = node.generate_id()

    assert id1 != id2
