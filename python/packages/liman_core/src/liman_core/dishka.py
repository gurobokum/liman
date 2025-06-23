from collections.abc import Callable
from inspect import (
    iscoroutinefunction,
)
from typing import TypeVar

from dishka import (
    Provider,
    Scope,
    make_async_container,
    make_container,
    provide,
)
from dishka.integrations.base import wrap_injection

from liman_core.registry import Registry


class LimanProvider(Provider):
    @provide(scope=Scope.APP)
    def get_registry(self) -> Registry:
        """
        Provides a singleton instance of the Registry.

        Returns:
            Registry: The singleton instance of the Registry.
        """
        return Registry()


liman_provider = LimanProvider()

container = make_container(liman_provider)
async_container = make_async_container(liman_provider)

T = TypeVar("T")


def inject(
    func: Callable[..., T],
) -> Callable[..., T]:
    is_async = bool(iscoroutinefunction(func))

    if is_async:
        injected_func = wrap_injection(
            func=func,
            is_async=True,
            container_getter=lambda *_: async_container,
            manage_scope=True,
        )
    else:
        injected_func = wrap_injection(
            func=func,
            is_async=False,
            container_getter=lambda *_: container,
            manage_scope=True,
        )

    return injected_func
