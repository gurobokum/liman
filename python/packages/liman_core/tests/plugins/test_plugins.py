from __future__ import annotations

from typing import Any

import pytest

from liman_core.plugins import PluginConflictError
from liman_core.plugins.core.base import Plugin
from liman_core.registry import DEFAULT_PLUGINS, Registry


class MockPlugin(Plugin):
    def __init__(self, name: str, registered_kinds: list[str], applies_to: list[str]):
        self.name = name
        self.registered_kinds = registered_kinds
        self.applies_to = applies_to
        self.field_name = "mock_field"
        self.field_type = str

    def validate(self, spec_data: Any) -> Any:
        return spec_data

    def apply(self, instance: Any) -> None: ...


def test_get_plugins_existing_kind(registry: Registry) -> None:
    plugins = registry.get_plugins("LLMNode")
    assert len(plugins) == len(DEFAULT_PLUGINS)


def test_get_plugins_nonexistent_kind(registry: Registry) -> None:
    plugins = registry.get_plugins("NonexistentKind")
    assert plugins == []


def test_add_plugins_with_registered_kinds(registry: Registry) -> None:
    plugin = MockPlugin("test_plugin", ["NewKind"], [])

    with pytest.raises(KeyError):
        registry.add_plugins([plugin])


def test_add_plugins_with_applies_to(registry: Registry) -> None:
    plugin = MockPlugin("test_plugin", [], ["LLMNode"])
    registry.add_plugins([plugin])

    assert plugin in registry._plugins["LLMNode"]


def test_add_plugins_conflict_with_registered_kinds(registry: Registry) -> None:
    plugin = MockPlugin("test_plugin", ["LLMNode"], [])

    with pytest.raises(PluginConflictError):
        registry.add_plugins([plugin])


def test_add_plugins_applies_to_unsupported_kind(registry: Registry) -> None:
    plugin = MockPlugin("test_plugin", [], ["UnsupportedKind"])

    with pytest.raises(PluginConflictError):
        registry.add_plugins([plugin])
