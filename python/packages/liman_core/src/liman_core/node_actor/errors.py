from liman_core.errors import LimanError


class NodeActorError(LimanError):
    """
    Errors specific to NodeActor execution
    """

    code: str = "node_actor_error"
