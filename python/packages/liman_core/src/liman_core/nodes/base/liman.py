from typing import Any

from .execution_context import ExecutionContext


class Liman:
    def __init__(self, execution_context: ExecutionContext[Any]) -> None:
        self.execution_context = execution_context

    def set(self) -> None: ...

    def get(self, key: str) -> Any:
        return getattr(self.execution_context, key)
