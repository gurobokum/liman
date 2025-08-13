import os

from liman.conf import enable_debug

if os.getenv("LIMAN_DEBUG") == "1":
    enable_debug()


from liman.executor.base import Executor

# Don't update the version manually, it is set by the build system.
__version__ = "0.1.0-a1"

__all__ = [
    "enable_debug",
    "Executor",
]
