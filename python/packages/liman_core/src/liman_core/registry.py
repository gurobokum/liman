from typing import Any, TypeVar

from liman_core.base import BaseNode
from liman_core.errors import LimanError

T = TypeVar("T", bound=BaseNode[Any])


class Registry:
    """
    A registry that stores nodes and allows for retrieval by name.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, BaseNode[Any]] = {}

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
            raise LimanError(f"Node with key '{key}' not found in the registry.")

    def add(self, node: BaseNode[Any]) -> None:
        """
        Add a node to the registry.

        Args:
            node (BaseNode): The node to add to the registry.
        """
        key = f"{node.kind}:{node.name}"
        if self._nodes.get(key):
            raise LimanError(f"Node with key '{key}' already exists in the registry.")
        self._nodes[key] = node
