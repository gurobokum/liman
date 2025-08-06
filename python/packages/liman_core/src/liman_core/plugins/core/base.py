from abc import abstractmethod
from typing import Any, Protocol, runtime_checkable


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
