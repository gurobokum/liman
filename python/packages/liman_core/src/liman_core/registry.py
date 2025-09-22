from __future__ import annotations

from typing import Any, TypeVar

from liman_core.base.component import Component
from liman_core.dishka import Scope, get_root_container
from liman_core.errors import ComponentNotFoundError, LimanError
from liman_core.plugins import PluginConflictError
from liman_core.plugins.auth.plugin import AuthPlugin
from liman_core.plugins.core.base import Plugin

T = TypeVar("T", bound="Component[Any]")
D = TypeVar("D")


DEFAULT_PLUGINS = [AuthPlugin()]


class Registry:
    """
    A registry that stores nodes and allows for retrieval by name.
    """

    def __init__(self) -> None:
        self._components: dict[str, Component[Any]] = {}

        self._plugins_kinds: set[str] = {"Node", "LLMNode", "ToolNode"}
        self._plugins: dict[str, list[Plugin]] = {
            kind: [*DEFAULT_PLUGINS] for kind in self._plugins_kinds
        }
        self.container = get_root_container()(scope=Scope.REGISTRY).container

    def add_plugins(self, plugins: list[Plugin]) -> None:
        """
        Add a list of plugins to the registry.

        Args:
            plugins (list[Plugin]): List of Plugin instances to add.
        """
        for plugin in plugins:
            for kind in plugin.registered_kinds:
                if kind in self._plugins_kinds:
                    raise PluginConflictError(
                        "Kind is already registered: {kind}", plugin_name=plugin.name
                    )
                self._plugins[kind].append(plugin)

            for applied_kind in plugin.applies_to:
                if applied_kind not in self._plugins_kinds:
                    raise PluginConflictError(
                        "Applied kind is not supported: {applied_kind}",
                        plugin_name=plugin.name,
                    )
                if not self._plugins.get(applied_kind):
                    self._plugins[applied_kind] = []
                self._plugins[applied_kind].append(plugin)

    def get_plugins(self, kind: str) -> list[Plugin]:
        """
        Retrieve the list of registered plugins.

        Returns:
            list[Plugin]: List of Plugin instances.
        """
        return self._plugins.get(kind, [])

    def lookup(self, kind: type[T], name: str) -> T:
        """
        Retrieve a component by its name.

        Args:
            name (str): The name of the component to retrieve.

        Returns:
            Component: The component associated with the given name.
        """
        key = f"{kind.__name__}:{name}"
        if key in self._components:
            node = self._components[key]

            if not isinstance(node, kind):
                raise TypeError(
                    f"Retrieved node '{node.name}' is of type {node.__class__.__name__}, "
                    f"but expected type {kind.__name__}."
                )
            return node
        else:
            raise ComponentNotFoundError(
                f"Component with key '{key}' not found in the registry."
            )

    def add(self, node: Component[Any]) -> None:
        """
        Add a component to the registry.

        Args:
            component (Component): The component to add to the registry.
        """
        key = f"{node.spec.kind}:{node.name}"
        if self._components.get(key):
            raise LimanError(f"Node with key '{key}' already exists in the registry.")
        self._components[key] = node

    def print_specs(self, initial: bool = False) -> None:
        """
        Print all registered components as YAML with --- separators, sorted by kind.

        Args:
            initial: If True, print initial data; otherwise, print validated specs.
        """
        if not self._components:
            return

        delim = "---"

        # Group components by kind
        components_by_kind: dict[str, list[Component[Any]]] = {}
        for component in self._components.values():
            kind = component.spec.kind
            if kind not in components_by_kind:
                components_by_kind[kind] = []
            components_by_kind[kind].append(component)

        # Sort components within each kind by name
        for components in components_by_kind.values():
            components.sort(key=lambda c: c.name)

        # Print known kinds in order
        kind_order = ["LLMNode", "ToolNode", "FunctionNode"]
        first_component = True
        for kind in kind_order:
            if kind not in components_by_kind:
                continue

            for component in components_by_kind[kind]:
                if not first_component:
                    print(f"{delim}\n")
                component.print_spec(initial=initial)
                first_component = False

        # Print remaining kinds (others) sorted alphabetically
        remaining_kinds = sorted(k for k in components_by_kind if k not in kind_order)
        for kind in remaining_kinds:
            for component in components_by_kind[kind]:
                if not first_component:
                    print(f"{delim}\n")
                component.print_spec(initial=initial)
                first_component = False
