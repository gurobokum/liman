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
    to: list[str | EdgeSpec] = []
    tools: list[str] = []

    @model_validator(mode="after")
    def validate_routing(self) -> Self:
        check_exclusive_routing(self)
        return self


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
