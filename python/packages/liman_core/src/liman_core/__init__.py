from liman_core.base import BaseNode
from liman_core.llm_node import LLMNode
from liman_core.tool_node import ToolNode

try:
    from liman_finops import configure_instrumentor

    configure_instrumentor(console=True)
    FINOPS_ENABLED = True
except ImportError:
    FINOPS_ENABLED = False
    raise


with open("VERSION") as fd:
    __version__ = fd.read().strip()

__all__ = [
    "BaseNode",
    "LLMNode",
    "ToolNode",
]
