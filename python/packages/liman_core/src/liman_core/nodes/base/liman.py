from typing import Any

from .execution_context import ExecutionContext


class Liman:
    """
    Core Liman runtime interface for accessing execution context.

    Provides a simplified interface for interacting with the execution
    context during node execution. Acts as a facade over ExecutionContext.
    """

    def __init__(self, execution_context: ExecutionContext[Any], **kwargs: Any) -> None:
        """
        Initialize Liman with execution context.

        Args:
            execution_context: The execution context for this runtime
        """
        self.execution_context = execution_context
        self._kwargs = kwargs or {}

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

    def __getattr__(self, key: str) -> Any:
        return self._kwargs[key]
