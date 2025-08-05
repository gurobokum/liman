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
