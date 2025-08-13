from __future__ import annotations

from enum import Enum
from typing import Any, Generic, NamedTuple
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from liman_core.nodes.base.node import BaseNode
from liman_core.nodes.base.schemas import NS


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


class Result(BaseModel):
    """
    Represents the output of a node execution.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    output: Any
    next_nodes: list[NextNode] = []


class NextNode(NamedTuple):
    """
    Represents a next node in the execution flow.
    """

    node: BaseNode[Any, Any]
    input_: Any
