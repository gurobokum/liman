class NodeActorState:
    """
    Represents the current state of a NodeActor
    """

    IDLE = "idle"

    INITIALIZING = "initializing"
    READY = "ready"
    EXECUTING = "executing"

    COMPLETED = "completed"
    SHUTDOWN = "shutdown"
