import sys
from typing import Any, Literal

from langchain_core.messages import BaseMessage
from pydantic import model_validator

from liman_core.base.schemas import BaseSpec
from liman_core.edge.schemas import EdgeSpec, check_exclusive_routing
from liman_core.languages import LocalizedValue
from liman_core.nodes.base.schemas import NodeState as BaseNodeState

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


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
    to: list[str | EdgeSpec] = []
    tools: list[str] = []

    @model_validator(mode="after")
    def validate_routing(self) -> Self:
        check_exclusive_routing(self)
        return self


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
