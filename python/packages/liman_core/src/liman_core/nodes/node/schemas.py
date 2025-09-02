from typing import Any, Literal

from langchain_core.messages import BaseMessage

from liman_core.base.schemas import BaseSpec
from liman_core.edge.schemas import EdgeSpec
from liman_core.languages import LocalizedValue
from liman_core.nodes.base.schemas import NodeState as BaseNodeState


class NodeSpec(BaseSpec):
    """
    Specification schema for generic custom nodes.

    Defines the configuration for custom nodes that implement
    specialized logic not covered by LLM or Tool nodes.
    """

    kind: Literal["Node"] = "Node"
    name: str
    func: str

    description: LocalizedValue | None = None
    prompts: LocalizedValue | None = None

    nodes: list[str | EdgeSpec] = []
    llm_nodes: list[str | EdgeSpec] = []
    tools: list[str] = []


class NodeState(BaseNodeState):
    """
    Runtime state for generic custom nodes.

    Maintains execution state including input/output data and
    message history for custom node execution.
    """

    kind: Literal["Node"] = "Node"

    messages: list[BaseMessage] = []
    input_: Any | None = None
    output: Any | None = None
