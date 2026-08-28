import os

from liman.conf import enable_debug

if os.getenv("LIMAN_DEBUG") == "1":
    enable_debug()


from liman_core.llm import get_llm
from liman_core.registry import Registry

from liman.agent import Agent
from liman.executor.base import Executor
from liman.loader import load_specs_from_directory
from liman.state import InMemoryStateStorage, StateStorage

# Don't update the version manually, it is set by the build system.
__version__ = "0.1.0-a4"

__all__ = [
    "Agent",
    "enable_debug",
    "Executor",
    "StateStorage",
    "InMemoryStateStorage",
    "Registry",
    "get_llm",
    "load_specs_from_directory",
]
