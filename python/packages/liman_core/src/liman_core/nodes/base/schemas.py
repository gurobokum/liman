from typing import Annotated, Any, TypeVar

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel, ConfigDict, Field


class NodeOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    response: "LangChainMessage"


class NodeInput(BaseModel):
    input_: Any


class NodeState(BaseModel):
    """
    State for Node.
    This class can be extended to add custom state attributes.
    """

    context: dict[str, Any] = {}


NS = TypeVar("NS", bound=NodeState)


LangChainMessage = Annotated[
    AIMessage | HumanMessage | ToolMessage, Field(discriminator="type")
]
