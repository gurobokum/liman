import os

from liman.conf import enable_debug

if os.getenv("LIMAN_DEBUG") == "1":
    enable_debug()


from liman.executor.base import Executor

__all__ = [
    "enable_debug",
    "Executor",
]
