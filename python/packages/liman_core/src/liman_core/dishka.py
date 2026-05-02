from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, TypeVar

from dishka import AsyncContainer, BaseScope, Provider, make_async_container, new_scope

T = TypeVar("T")

DI_VAR_PREFIX = "__from_liman__"


class Scope(BaseScope):
    APP = new_scope("APP")
    REGISTRY = new_scope("REGISTRY")
    NODE = new_scope("NODE")


class LimanProvider(Provider): ...


def make_container(provider: LimanProvider) -> AsyncContainer:
    return make_async_container(provider, scopes=Scope)


@dataclass
class DependencyMarker:
    dependency_type: type
    _is_from_liman: Literal[True] = True


if TYPE_CHECKING:
    from typing import Union

    FromLiman = Union[T, T]  # noqa: UP007,PYI016
else:

    class FromLiman:
        """
        FastAPI-like dependency injection for Liman nodes using dishka.

        Usage:
            # 1. Register factory in registry
            def get_database() -> Database:
                return Database("production")

            registry.provide(get_database, scope=Scope.NODE)

            # 2. Use in tool function
            def my_tool(
                message: str,
                db: FromLiman[Database]
            ) -> str:
                return f"Message: {message}, DB: {db.name}"

        The type annotation FromLiman[Database] tells the system:
        - To inject a Database instance
        - Resolved through dishka's dependency injection system
        """

        def __class_getitem__(cls, dependency_type: type[T]) -> DependencyMarker:
            return DependencyMarker(dependency_type=dependency_type)


def is_from_liman_dependency(param_type: Any) -> bool:
    """
    Check if a parameter type is a FromLiman dependency.

    Args:
        param_type: Type annotation to check

    Returns:
        True if it's a FromLiman dependency
    """
    return hasattr(param_type, "_is_from_liman")


async def resolve_from_liman_dependency(param_type: Any, container: Any) -> Any:
    """
    Resolve a FromLiman dependency using dishka container.

    Args:
        param_type: The dependency marker type
        container: Dishka container for dependency resolution

    Returns:
        Resolved dependency instance
    """
    if not is_from_liman_dependency(param_type):
        raise ValueError(f"Type {param_type} is not a FromLiman dependency")

    dependency_type = param_type.dependency_type
    return await container.get(dependency_type)
