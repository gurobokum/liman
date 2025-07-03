from typing import Any


class LimanError(Exception):
    """Base class for all Liman errors."""

    def __init__(
        self, message: str, code: str | int | None = None, **kwargs: Any
    ) -> None:
        super().__init__(message)
        self.code = code
        self.kwargs = kwargs


class InvalidSpecError(LimanError):
    """Raised when a node specification is invalid."""

    code: str = "invalid_spec"
