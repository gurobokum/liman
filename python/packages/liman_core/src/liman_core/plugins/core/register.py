from liman_core.plugins.core.base import Plugin
from liman_core.registry import Registry


def register_plugins(plugins: list[Plugin], registry: Registry) -> None:
    """
    Register a list of plugins into the global registry.

    Args:
        plugins (list[Plugin]): List of Plugin instances to register.
    """
    ...
