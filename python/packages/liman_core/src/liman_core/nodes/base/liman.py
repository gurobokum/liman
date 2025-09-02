from typing import Any

from .execution_context import ExecutionContext


class Liman:
    """
    Core Liman runtime interface for accessing execution context.

    Provides a simplified interface for interacting with the execution
    context during node execution. Acts as a facade over ExecutionContext.
    """

    def __init__(self, execution_context: ExecutionContext[Any]) -> None:
        """
        Initialize Liman with execution context.

        Args:
            execution_context: The execution context for this runtime
        """
        self.execution_context = execution_context

    def set(self) -> None: ...

    def get(self, key: str) -> Any:
        """
        Get attribute from execution context.

        Args:
            key: Attribute name to retrieve

        Returns:
            Value of the requested attribute
        """
        return getattr(self.execution_context, key)
