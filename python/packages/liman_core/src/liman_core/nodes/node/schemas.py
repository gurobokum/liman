from typing import Any, Literal

from langchain_core.messages import BaseMessage

from liman_core.base.schemas import BaseSpec
from liman_core.edge.schemas import EdgeSpec
from liman_core.languages import LocalizedValue
from liman_core.nodes.base.schemas import NodeState as BaseNodeState


class NodeSpec(BaseSpec):
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
    State for Node.
    """

    messages: list[BaseMessage] = []
    input_: Any | None = None
    output: Any | None = None
