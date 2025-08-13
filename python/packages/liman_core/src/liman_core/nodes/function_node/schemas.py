from typing import Any, Literal

from langchain_core.messages import BaseMessage

from liman_core.base.schemas import BaseSpec
from liman_core.edge.schemas import EdgeSpec
from liman_core.languages import LocalizedValue
from liman_core.nodes.base.schemas import NodeState as BaseNodeState


class FunctionNodeSpec(BaseSpec):
    kind: Literal["FunctionNode"] = "FunctionNode"
    name: str
    func: str | None = None

    description: LocalizedValue | None = None
    prompts: LocalizedValue | None = None

    nodes: list[str | EdgeSpec] = []
    llm_nodes: list[str | EdgeSpec] = []
    tools: list[str] = []


class FunctionNodeState(BaseNodeState):
    kind: Literal["FunctionNode"] = "FunctionNode"
    name: str

    messages: list[BaseMessage] = []
    input_: Any | None = None
    output: Any | None = None
