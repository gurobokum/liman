from typing import Any


class LimanError(Exception):
    """Base class for all Liman errors."""

    def __init__(
        self, message: str, code: str | int | None = None, **kwargs: Any
    ) -> None:
        super().__init__(message)
        if code:
            self.code = code
        self.kwargs = kwargs

    def __getitem__(self, item: str) -> Any:
        """Get attribute or return None if it doesn't exist."""
        return self.kwargs.get(item, None)


class InvalidSpecError(LimanError):
    """Raised when a node specification is invalid."""

    code: str = "invalid_spec"


class ComponentNotFoundError(LimanError):
    """Raised when a component is not found in the registry."""

    code: str = "component_not_found"
