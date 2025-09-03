from typing import Any


def noop(*args: Any, **kwargs: Any) -> None:
    """
    No-operation function
    Accepts any arguments and returns None.

    Args:
        *args: Any positional arguments (ignored)
        **kwargs: Any keyword arguments (ignored)
    """
    pass
