from typing import Any, TypeVar

from liman_core.base import BaseNode
from liman_core.errors import LimanError
from liman_core.plugins import PluginConflictError
from liman_core.plugins.core.base import Plugin

T = TypeVar("T", bound=BaseNode[Any])


class NodeNotFoundError(LimanError):
    """Raised when a node is not found in the registry."""

    code: str = "node_not_found"


class Registry:
    """
    A registry that stores nodes and allows for retrieval by name.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, BaseNode[Any]] = {}

        self._supported_kinds: set[str] = {"Node", "LLMNode", "ToolNode"}
        self._plugins: dict[str, list[Plugin]] = {
            kind: [] for kind in self._supported_kinds
        }

    def add_plugins(self, plugins: list[Plugin]) -> None:
        """
        Add a list of plugins to the registry.

        Args:
            plugins (list[Plugin]): List of Plugin instances to add.
        """
        for plugin in plugins:
            for kind in plugin.registered_kinds:
                if kind in self._supported_kinds:
                    raise PluginConflictError(
                        "Kind is already registered: {kind}", plugin_name=plugin.name
                    )
                self._plugins[kind].append(plugin)

            for applied_kind in plugin.applies_to:
                if applied_kind not in self._supported_kinds:
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
        Retrieve a node by its name.

        Args:
            name (str): The name of the node to retrieve.

        Returns:
            BaseNode: The node associated with the given name.
        """
        key = f"{kind.__name__}:{name}"
        if key in self._nodes:
            node = self._nodes[key]

            if not isinstance(node, kind):
                raise TypeError(
                    f"Retrieved node '{node.name}' is of type {node.__class__.__name__}, "
                    f"but expected type {kind.__name__}."
                )
            return node
        else:
            raise NodeNotFoundError(f"Node with key '{key}' not found in the registry.")

    def add(self, node: BaseNode[Any]) -> None:
        """
        Add a node to the registry.

        Args:
            node (BaseNode): The node to add to the registry.
        """
        key = f"{node.spec.kind}:{node.name}"
        if self._nodes.get(key):
            raise LimanError(f"Node with key '{key}' already exists in the registry.")
        self._nodes[key] = node
