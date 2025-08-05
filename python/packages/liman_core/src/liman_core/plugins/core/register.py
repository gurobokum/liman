from dishka import FromDishka

from liman_core.dishka import inject
from liman_core.plugins.core.base import Plugin
from liman_core.registry import Registry


@inject
def register_plugins(plugins: list[Plugin], registry: FromDishka[Registry]) -> None:
    """
    Register a list of plugins into the global registry.

    Args:
        plugins (list[Plugin]): List of Plugin instances to register.
    """
    ...
