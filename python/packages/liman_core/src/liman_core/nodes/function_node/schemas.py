from typing import Any, Literal

from langchain_core.messages import BaseMessage

from liman_core.base.schemas import BaseSpec
from liman_core.edge.schemas import EdgeSpec
from liman_core.languages import LocalizedValue
from liman_core.nodes.base.schemas import NodeState as BaseNodeState


class FunctionNodeSpec(BaseSpec):
    """
    Specification schema for function nodes.

    Defines the configuration for custom function nodes including
    function reference, descriptions, and connected nodes.
    """

    kind: Literal["FunctionNode"] = "FunctionNode"
    name: str
    func: str | None = None

    description: LocalizedValue | None = None
    prompts: LocalizedValue | None = None

    nodes: list[str | EdgeSpec] = []
    llm_nodes: list[str | EdgeSpec] = []
    tools: list[str] = []


class FunctionNodeState(BaseNodeState):
    """
    Runtime state for function nodes.

    Maintains execution state including input/output data and
    message history for function node execution.
    """

    kind: Literal["FunctionNode"] = "FunctionNode"
    name: str

    messages: list[BaseMessage] = []
    input_: Any | None = None
    output: Any | None = None
