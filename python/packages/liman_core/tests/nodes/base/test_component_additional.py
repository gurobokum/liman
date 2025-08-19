import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from liman_core.base.component import Component, _preserve_multiline_strings
from liman_core.base.schemas import BaseSpec
from liman_core.errors import InvalidSpecError
from liman_core.plugins.core.base import Plugin
from liman_core.registry import Registry


class MockComponentSpec(BaseSpec):
    kind: str = "MockComponent"
    name: str
    description: str | None = None


class MockComponent(Component[MockComponentSpec]):
    spec_type = MockComponentSpec

    def compile(self) -> None:
        pass


class MockPlugin(Plugin):
    def __init__(self, field_name: str, applies_to: list[str]) -> None:
        self.name = "mock_plugin"
        self.applies_to = applies_to
        self.registered_kinds: list[str] = []

        self.field_name = field_name
        self.field_type = str

    def validate(self, spec_data: Any) -> Any:
        return spec_data


def test_component_full_name(registry: Registry) -> None:
    spec = MockComponentSpec(kind="TestKind", name="test_component")
    component = MockComponent(spec, registry)

    assert component.full_name == "TestKind/test_component"


def test_component_from_yaml_path_pathlib_path(registry: Registry) -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("kind: MockComponent\nname: test_component\n")
        temp_path = Path(f.name)

    try:
        component = MockComponent.from_yaml_path(temp_path, registry)

        assert component.name == "test_component"
        assert component.yaml_path == str(temp_path)
    finally:
        temp_path.unlink()


def test_component_from_yaml_path_invalid_yaml_content(registry: Registry) -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("- this is a list not a dict\n")
        temp_path = Path(f.name)

    try:
        with pytest.raises(InvalidSpecError) as exc_info:
            MockComponent.from_yaml_path(temp_path, registry)

        assert "YAML content must be a dictionary at the top level" in str(
            exc_info.value
        )
    finally:
        temp_path.unlink()


def test_create_extended_spec_no_plugins(registry: Registry) -> None:
    data = {"kind": "MockComponent", "name": "test"}

    result = MockComponent.create_extended_spec(MockComponentSpec, [], data)

    assert result is MockComponentSpec


def test_create_extended_spec_no_kind_in_data(registry: Registry) -> None:
    plugins = [MockPlugin("test_field", ["MockComponent"])]
    data = {"name": "test"}

    with pytest.raises(InvalidSpecError) as exc_info:
        MockComponent.create_extended_spec(MockComponentSpec, plugins, data)

    assert "Spec data must contain 'kind' field" in str(exc_info.value)


def test_create_extended_spec_plugin_not_applicable(registry: Registry) -> None:
    plugins = [MockPlugin("test_field", ["DifferentKind"])]
    data = {"kind": "MockComponent", "name": "test"}

    result = MockComponent.create_extended_spec(MockComponentSpec, plugins, data)

    assert result is MockComponentSpec


def test_create_extended_spec_with_valid_plugin(registry: Registry) -> None:
    plugins = [MockPlugin("custom_field", ["MockComponent"])]
    data = {"kind": "MockComponent", "name": "test"}

    result = MockComponent.create_extended_spec(MockComponentSpec, plugins, data)

    assert result != MockComponentSpec
    assert "WithPlugins" in result.__name__
    # Check if the field exists in the model fields
    assert "custom_field" in result.model_fields


def test_create_extended_spec_multiple_plugins(registry: Registry) -> None:
    plugins = [
        MockPlugin("field1", ["MockComponent"]),
        MockPlugin("field2", ["MockComponent"]),
    ]
    data = {"kind": "MockComponent", "name": "test"}

    result = MockComponent.create_extended_spec(MockComponentSpec, plugins, data)

    assert "field1" in result.model_fields
    assert "field2" in result.model_fields


@patch("liman_core.base.component.rich_print")
def test_component_print_spec_initial_false(
    mock_print: Mock, registry: Registry
) -> None:
    spec = MockComponentSpec(kind="MockComponent", name="test_component")
    component = MockComponent(
        spec, registry, initial_data={"kind": "MockComponent", "name": "test_component"}
    )

    component.print_spec(initial=False)

    mock_print.assert_called_once()


@patch("liman_core.base.component.rich_print")
def test_component_print_spec_initial_true(
    mock_print: Mock, registry: Registry
) -> None:
    initial_data = {
        "kind": "MockComponent",
        "name": "test_component",
        "description": "Initial",
    }
    spec = MockComponentSpec(kind="MockComponent", name="test_component")
    component = MockComponent(spec, registry, initial_data=initial_data)

    component.print_spec(initial=True)

    mock_print.assert_called_once()


def test_preserve_multiline_strings_none() -> None:
    result = _preserve_multiline_strings(None)

    assert result is None


def test_preserve_multiline_strings_single_line() -> None:
    data = "single line string"

    result = _preserve_multiline_strings(data)

    assert result == data


def test_preserve_multiline_strings_multiline() -> None:
    data = "line1\nline2\nline3"

    result = _preserve_multiline_strings(data)

    # Should be converted to PreservedScalarString
    assert str(result) == data
    assert hasattr(result, "__class__")


def test_preserve_multiline_strings_dict() -> None:
    data = {
        "single": "single line",
        "multi": "line1\nline2",
        "nested": {"inner_multi": "a\nb\nc"},
    }

    result = _preserve_multiline_strings(data)

    assert result
    assert isinstance(result, dict)
    assert result["single"] == "single line"
    assert str(result["multi"]) == "line1\nline2"
    assert str(result["nested"]["inner_multi"]) == "a\nb\nc"


def test_component_repr(registry: Registry) -> None:
    spec = MockComponentSpec(kind="MockComponent", name="test_component")
    component = MockComponent(spec, registry)

    result = repr(component)

    assert result == "MockComponent:test_component"


def test_component_generate_id_unique(registry: Registry) -> None:
    spec = MockComponentSpec(kind="MockComponent", name="test_component")
    component = MockComponent(spec, registry)

    id1 = component.generate_id()
    id2 = component.generate_id()

    assert id1 != id2
