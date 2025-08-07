from typing import Any

from pydantic import BaseModel


class NodeActorStatus:
    """
    Represents the current status of a NodeActor
    """

    IDLE = "idle"

    INITIALIZING = "initializing"
    READY = "ready"
    EXECUTING = "executing"

    COMPLETED = "completed"
    SHUTDOWN = "shutdown"


class NodeActorState(BaseModel):
    input_: Any
    output: Any | None = None
    context: dict[str, Any] | None = None
