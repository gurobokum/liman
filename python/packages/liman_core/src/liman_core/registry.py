from liman_core.base import BaseNode
from liman_core.errors import LimanError


class Registry:
    """
    A registry that stores nodes and allows for retrieval by name.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, BaseNode] = {}

    def lookup(self, kind: BaseNode, name: str) -> BaseNode:
        """
        Retrieve a node by its name.

        Args:
            name (str): The name of the node to retrieve.

        Returns:
            BaseNode: The node associated with the given name.
        """
        key = f"{kind}:{name}"
        if name in self._nodes:
            return self._nodes[key]
        else:
            raise LimanError(f"Node with key '{key}' not found in the registry.")

    def add(self, node: BaseNode) -> None:
        """
        Add a node to the registry.

        Args:
            node (BaseNode): The node to add to the registry.
        """
        key = f"{node.kind}:{node.name}"
        if self._nodes.get(key):
            raise LimanError(f"Node with key '{key}' already exists in the registry.")
        self._nodes[key] = node
