from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from liman_core.base.component import Component

if TYPE_CHECKING:
    from liman_core.registry import Registry


@runtime_checkable
class Plugin(Protocol):
    """
    Plugin interface for extending Liman specifications with additional functionality.
    """

    # Unique plugin identifier
    name: str
    # Spec types this plugin extends (e.g., ['Node', 'LLMNode'])
    applies_to: list[str]
    # Kinds this plugin supports (e.g., ['ServiceAccount', 'Metrics'])
    registered_kinds: list[str]
    # Field name added to specifications
    field_name: str
    # Field structure type (e.g., Pydantic model)
    field_type: type

    @abstractmethod
    def validate(self, spec_data: Any) -> Any:
        """
        Validate and transform plugin-specific data
        """
        ...


@runtime_checkable
class ExecutionStateProvider(Protocol):
    """
    Protocol for plugins that provide execution state management.
    """

    @abstractmethod
    def get_execution_state(
        self, component: Component[Any], state: dict[str, Any], registry: Registry
    ) -> dict[str, Any]:
        """
        Get the execution state based on the provided one
        """
        ...
