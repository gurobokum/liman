from abc import ABC, abstractmethod
from collections.abc import Coroutine
from typing import Any
from uuid import UUID, uuid4

from langchain_core.language_models.chat_models import BaseChatModel

from liman_core.base import BaseNode, Output
from liman_core.node_actor.errors import NodeActorError
from liman_core.node_actor.schemas import NodeActorStatus
from liman_core.utils import to_snake_case


class BaseNodeActor(ABC):
    """
    Base class for NodeActor implementations providing shared functionality.

    Each NodeActor is responsible for:
    - Managing the lifecycle of a single node
    - Executing the node with proper error handling
    - Providing execution interface (sync/async)
    """

    def __init__(
        self,
        node: BaseNode[Any],
        actor_id: UUID | None = None,
        llm: BaseChatModel | None = None,
    ):
        self.id = actor_id or uuid4()
        self.node = node
        self.llm = llm

        self.status = NodeActorStatus.IDLE
        self.error: NodeActorError | None = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, node={self.node.name}, status={self.status})"

    @property
    def composite_id(self) -> str:
        """
        Standardized composite identifier in format: actor_type/node_type/node_name/uuid
        """
        actor_type = to_snake_case(self.__class__.__name__)
        node_type = to_snake_case(self.node.__class__.__name__)
        node_name = self.node.name
        return f"{actor_type}/{node_type}/{node_name}/{self.id}"

    def get_status(self) -> dict[str, Any]:
        """
        Get current actor status
        """
        return {
            "actor_id": str(self.id),
            "node_name": self.node.name,
            "node_type": self.node.spec.kind,
            "status": self.status,
            "is_shutdown": self._is_shutdown(),
        }

    def _prepare_execution_context(
        self, context: dict[str, Any], execution_id: UUID
    ) -> dict[str, Any]:
        """
        Prepare execution context with actor metadata
        """
        execution_context = {
            **context,
            "actor_id": self.id,
            "execution_id": execution_id,
            "node_name": self.node.name,
            "node_type": self.node.spec.kind,
        }

        return execution_context

    @abstractmethod
    def initialize(self) -> None | Coroutine[None, None, None]:
        """
        Initialize the actor and prepare for execution
        """
        ...

    @abstractmethod
    def execute(
        self,
        input_: Any,
        context: dict[str, Any] | None = None,
        execution_id: UUID | None = None,
    ) -> Output[Any] | Coroutine[None, None, Output[Any]]:
        """
        Execute the wrapped node with the provided inputs
        """
        ...

    @abstractmethod
    def shutdown(self) -> None | Coroutine[None, None, None]:
        """
        Gracefully shutdown the actor
        """
        ...

    @abstractmethod
    def _is_shutdown(self) -> bool:
        """
        Check if actor is shutdown
        """
        ...


def create_error(
    message: str, actor: "BaseNodeActor", *, execution_id: UUID | None = None
) -> NodeActorError:
    return NodeActorError(
        message,
        actor_id=actor.id,
        actor_composite_id=actor.composite_id,
        node_kind=actor.node.spec.kind,
        node_name=actor.node.name,
        execution_id=execution_id,
    )
