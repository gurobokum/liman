from typing import Annotated, Any, TypeVar

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel, Field


class NodeState(BaseModel):
    """
    Base state model for all nodes in the Liman framework.

    Provides common state attributes that all nodes require.
    Can be extended by specific node types to add custom state data.
    """

    kind: str
    name: str

    context: dict[str, Any] = {}


NS = TypeVar("NS", bound=NodeState)


LangChainMessage = AIMessage | HumanMessage | ToolMessage
LangChainMessageT = Annotated[LangChainMessage, Field(discriminator="type")]
