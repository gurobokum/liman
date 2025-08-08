from typing import Any, TypeVar

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, ConfigDict


class BaseSpec(BaseModel):
    kind: str
    name: str


class NodeOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    response: BaseMessage


class NodeState(BaseModel):
    """
    State for Node.
    This class can be extended to add custom state attributes.
    """

    context: dict[str, Any] = {}


S = TypeVar("S", bound=BaseSpec)
NS = TypeVar("NS", bound=NodeState)
