from typing import Any, Generic

from liman_core.nodes.base.schemas import NS


class ExecutionContext(Generic[NS]):
    def __init__(self, node_state: NS, **kwargs: Any) -> None:
        self.node_state = node_state
        self._context: dict[str, Any] = {}
        for key, value in kwargs.items():
            if key in self._context:
                raise AttributeError(
                    f"Attribute {key} already exists in ExecutionContext"
                )
            self._context[key] = value

    def __getitem__(self, key: str) -> Any:
        if key not in self._context:
            raise KeyError(f"Key {key} not found in ExecutionContext")

        return self._context[key]

    def __repr__(self) -> str:
        return f"ExecutionContext(__id={id(self)}, node_state={self.node_state}, _context={self._context})"
