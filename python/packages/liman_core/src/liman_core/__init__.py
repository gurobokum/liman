import os

from liman_core.conf import enable_debug

if os.getenv("LIMAN_DEBUG") == "1":
    enable_debug()

from liman_core.dishka import provide
from liman_core.node_actor import NodeActor
from liman_core.nodes.llm_node import LLMNode
from liman_core.nodes.tool_node import ToolNode
from liman_core.registry import Registry

# Don't update the version manually, it is set by the build system.
__version__ = "0.1.0-a4"

__all__ = ["LLMNode", "ToolNode", "NodeActor", "Registry", "provide"]
