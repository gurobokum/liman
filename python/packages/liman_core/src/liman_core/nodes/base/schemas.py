from typing import Annotated, Any, TypeVar

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel, Field


class NodeState(BaseModel):
    """
    State for Node.
    This class can be extended to add custom state attributes.
    """

    kind: str
    name: str

    context: dict[str, Any] = {}


NS = TypeVar("NS", bound=NodeState)


LangChainMessage = AIMessage | HumanMessage | ToolMessage
LangChainMessageT = Annotated[LangChainMessage, Field(discriminator="type")]
