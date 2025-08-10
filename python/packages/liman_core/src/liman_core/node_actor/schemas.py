from enum import Enum
from typing import Any, Generic
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from liman_core.base.schemas import S
from liman_core.nodes.base.node import BaseNode
from liman_core.nodes.base.schemas import NS, NodeOutput


class NodeActorStatus(str, Enum):
    """
    Represents the current status of a NodeActor
    """

    IDLE = "idle"

    INITIALIZING = "initializing"
    READY = "ready"
    EXECUTING = "executing"

    COMPLETED = "completed"
    SHUTDOWN = "shutdown"


class NodeActorState(BaseModel, Generic[NS]):
    actor_id: UUID
    node_id: UUID

    status: NodeActorStatus
    has_error: bool = False

    node_name: str
    node_state: NS
    node_type: str
    parent_node_name: str | None = None


class Result(BaseModel, Generic[S, NS]):
    """
    Represents the output of a node execution.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    node_output: NodeOutput
    next_nodes: list[tuple[BaseNode[S, NS], dict[str, Any]]] = []
