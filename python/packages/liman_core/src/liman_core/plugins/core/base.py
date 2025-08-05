from abc import abstractmethod
from typing import Any, Protocol


class Plugin(Protocol):
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique plugin identifier
        """
        ...

    @property
    @abstractmethod
    def applies_to(self) -> list[str]:
        """
        List of spec types this plugin extends (e.g., ['Node', 'LLMNode'])
        """
        ...

    @property
    @abstractmethod
    def registered_kinds(self) -> list[str]:
        """
        List of kinds this plugin supports that extends specifcations (e.g., ['ServiceAccount', 'Metrics'])
        """
        ...

    @property
    @abstractmethod
    def field_name(self) -> str:
        """
        Field name added to specifications
        """
        ...

    @property
    @abstractmethod
    def field_type(self) -> type:
        """
        Field structure type (e.g., Pydantic model in python)
        """
        ...

    @abstractmethod
    def validate(self, spec_data: Any) -> Any:
        """
        Validate and transform plugin-specific data
        """
        ...
