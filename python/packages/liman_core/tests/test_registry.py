from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest

from liman_core.base.component import Component
from liman_core.errors import ComponentNotFoundError, LimanError
from liman_core.registry import DEFAULT_PLUGINS, Registry


class MockComponent(Component[Any]):
    def __init__(self, name: str, kind: str) -> None:
        self.name = name
        self.spec = Mock()
        self.spec.name = name
        self.spec.kind = kind

    def compile(self) -> None: ...

    def print_spec(self, initial: bool = False) -> None:
        print(f"kind: {self.spec.kind}")
        print(f"name: {self.name}")


@pytest.fixture
def mock_component() -> MockComponent:
    return MockComponent("test_component", "MockComponent")


def test_registry_init(registry: Registry) -> None:
    assert registry._components == {}
    assert "Node" in registry._plugins_kinds
    assert "LLMNode" in registry._plugins_kinds
    assert "ToolNode" in registry._plugins_kinds
    assert len(registry._plugins["Node"]) == len(DEFAULT_PLUGINS)


def test_add_component(registry: Registry, mock_component: MockComponent) -> None:
    registry.add(mock_component)
    key = f"{mock_component.spec.kind}:{mock_component.name}"
    assert key in registry._components
    assert registry._components[key] == mock_component


def test_add_duplicate_component_raises_error(
    registry: Registry, mock_component: MockComponent
) -> None:
    registry.add(mock_component)

    with pytest.raises(LimanError) as exc_info:
        registry.add(mock_component)

    assert "already exists in the registry" in str(exc_info.value)


def test_lookup_existing_component(
    registry: Registry, mock_component: MockComponent
) -> None:
    registry.add(mock_component)
    result = registry.lookup(MockComponent, mock_component.name)
    assert result == mock_component


def test_lookup_nonexistent_component(registry: Registry) -> None:
    with pytest.raises(ComponentNotFoundError) as exc_info:
        registry.lookup(MockComponent, "nonexistent")

    assert "not found in the registry" in str(exc_info.value)


def test_print_specs_empty_registry(
    registry: Registry, capsys: pytest.CaptureFixture[str]
) -> None:
    registry.print_specs()
    captured = capsys.readouterr()
    assert captured.out == ""


def test_print_specs_with_components(
    registry: Registry, capsys: pytest.CaptureFixture[str]
) -> None:
    component1 = MockComponent("comp1", "LLMNode")
    component2 = MockComponent("comp2", "ToolNode")
    component3 = MockComponent("comp3", "LLMNode")

    registry.add(component1)
    registry.add(component2)
    registry.add(component3)

    registry.print_specs()
    captured = capsys.readouterr()

    assert "kind: LLMNode" in captured.out
    assert "kind: ToolNode" in captured.out
    assert "name: comp1" in captured.out
    assert "name: comp2" in captured.out
    assert "name: comp3" in captured.out
    assert "---" in captured.out
