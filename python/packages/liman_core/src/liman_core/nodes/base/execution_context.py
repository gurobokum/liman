from typing import Any, Generic

from liman_core.nodes.base.schemas import NS


class ExecutionContext(Generic[NS]):
    """
    Execution context for nodes containing state and runtime data.

    Generic container that holds node state and additional context data
    for node execution. Provides dictionary-like access to context data
    while maintaining type safety for the node state.
    """

    def __init__(self, node_state: NS, **kwargs: Any) -> None:
        """
        Initialize execution context with node state and additional data.

        Args:
            node_state: Node-specific state object
            **kwargs: Additional context data as key-value pairs

        Raises:
            AttributeError: If a key already exists in the context
        """
        self.node_state = node_state
        self._context: dict[str, Any] = {}
        for key, value in kwargs.items():
            if key in self._context:
                raise AttributeError(
                    f"Attribute {key} already exists in ExecutionContext"
                )
            self._context[key] = value

    def __getitem__(self, key: str) -> Any:
        """
        Get context data by key.

        Args:
            key: The key to retrieve from context

        Returns:
            Value associated with the key

        Raises:
            KeyError: If key is not found in context
        """
        if key not in self._context:
            raise KeyError(f"Key {key} not found in ExecutionContext")

        return self._context[key]

    def __repr__(self) -> str:
        """
        Return string representation of the execution context.

        Returns:
            String representation showing context ID, node state, and context data
        """
        return f"ExecutionContext(__id={id(self)}, node_state={self.node_state}, _context={self._context})"
