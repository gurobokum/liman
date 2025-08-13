from typing import Annotated, Any, Literal

from langchain_core.messages import ToolMessage
from pydantic import BaseModel, Field

from liman_core.base.schemas import BaseSpec
from liman_core.edge.schemas import EdgeSpec
from liman_core.languages import LocalizedValue
from liman_core.nodes.base.schemas import NodeState


class ToolArgument(BaseModel):
    name: str
    type: str
    description: LocalizedValue
    optional: bool = False


class ToolNodeSpec(BaseSpec):
    kind: Literal["ToolNode"] = "ToolNode"
    name: str
    description: LocalizedValue

    func: str | None = None
    arguments: list[ToolArgument] | None = None
    triggers: list[LocalizedValue] | None = None
    tool_prompt_template: LocalizedValue | None = None
    llm_nodes: list[EdgeSpec] = []


class ToolCall(BaseModel):
    name: str
    args: dict[str, Any]
    id_: Annotated[str | None, Field(alias="id")] = None
    type_: Literal["tool_call"] = "tool_call"


class ToolNodeState(NodeState):
    input_: ToolCall | None = None
    output: ToolMessage | None = None
