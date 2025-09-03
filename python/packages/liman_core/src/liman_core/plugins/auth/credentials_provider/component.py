from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

from liman_core.base.component import Component
from liman_core.base.utils import noop
from liman_core.errors import InvalidSpecError

from .schemas import CredentialsProviderSpec


class CredentialsProvider(Component[CredentialsProviderSpec]):
    spec_type = CredentialsProviderSpec

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.func = self._load_func()

    def _load_func(self) -> Callable[..., Any]:
        try:
            func_path = self.spec.func.split(".")
            module = import_module(".".join(func_path[:-1]))
            func = getattr(module, func_path[-1])
            if not callable(func):
                raise ValueError(
                    f"Function '{self.spec.func}' is not callable or does not exist."
                )
            return cast(Callable[..., Any], func)
        except (ImportError, ValueError) as e:
            if self.strict:
                raise InvalidSpecError(
                    f"Failed to import module for function '{self.spec.func}': {e}"
                ) from e
            return noop
