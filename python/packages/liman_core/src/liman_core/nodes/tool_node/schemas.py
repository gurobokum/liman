from typing import Annotated, Any, Literal

from langchain_core.messages import ToolMessage
from pydantic import BaseModel, Field

from liman_core.base.schemas import BaseSpec
from liman_core.edge.schemas import EdgeSpec
from liman_core.languages import LocalizedValue
from liman_core.nodes.base.schemas import NodeState


class ToolArgument(BaseModel):
    """
    Specification for a tool function argument.

    Defines the name, type, description, and optionality of a single
    argument that can be passed to a tool function.
    """

    name: str
    type: str | list[str]
    description: LocalizedValue | None = None
    optional: bool = False


class ToolObjectArgument(BaseModel):
    """
    Specification for a complex object argument with nested properties.

    Extends ToolArgument to support object types with nested properties,
    allowing for complex data structures as tool arguments.
    """

    name: str
    type: str
    description: LocalizedValue | None = None
    optional: bool = False
    properties: list[ToolArgument] | None = None


class ToolNodeSpec(BaseSpec):
    """
    Specification schema for tool nodes.

    Defines the complete configuration for a tool node including
    function reference, arguments, descriptions, and triggers.
    """

    kind: Literal["ToolNode"] = "ToolNode"
    name: str
    description: LocalizedValue | None = None

    func: str | None = None
    arguments: list[ToolArgument] | list[ToolObjectArgument] | None = None
    triggers: list[LocalizedValue] | None = None
    tool_prompt_template: LocalizedValue | None = None
    llm_nodes: list[EdgeSpec] = []


class ToolCall(BaseModel):
    """
    Represents a function call request from an LLM.

    Contains the tool name, arguments, and call ID needed to
    execute a tool function and track the response.
    """

    name: str
    args: dict[str, Any]
    id_: Annotated[str | None, Field(alias="id")] = None
    type_: Literal["tool_call"] = "tool_call"


class ToolNodeState(NodeState):
    """
    Runtime state for tool nodes.

    Maintains the current tool call input and output message
    for tracking execution state.
    """

    input_: ToolCall | None = None
    output: ToolMessage | None = None
