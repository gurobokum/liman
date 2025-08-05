import sys
import threading
from collections.abc import Sequence
from typing import Any
from uuid import UUID, uuid4

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

from liman_core.base import BaseNode, Output
from liman_core.llm_node.node import LLMNode
from liman_core.node.node import Node
from liman_core.node_actor.base import BaseNodeActor, create_error
from liman_core.node_actor.schemas import NodeActorStatus
from liman_core.tool_node.node import ToolNode

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class NodeActor(BaseNodeActor):
    """
    Sync implementation of NodeActor
    """

    def __init__(
        self,
        node: BaseNode[Any],
        actor_id: UUID | None = None,
        llm: BaseChatModel | None = None,
    ):
        super().__init__(node, actor_id, llm)
        self._execution_lock = threading.Lock()
        self._shutdown_event = threading.Event()

    @classmethod
    def create(
        cls,
        node: BaseNode[Any],
        actor_id: UUID | None = None,
        llm: BaseChatModel | None = None,
    ) -> Self:
        """
        Create a NodeActor instance from a node.

        Args:
            node: The node to wrap in this actor
            actor_id: Optional custom actor ID
            llm: Optional LLM instance for LLMNodes

        Returns:
            Configured NodeActor instance
        """
        actor = cls(node=node, actor_id=actor_id, llm=llm)
        return actor

    def _is_shutdown(self) -> bool:
        """Check if actor is shutdown"""
        return self._shutdown_event.is_set()

    def initialize(self) -> None:
        """
        Initialize the actor and prepare for execution
        """
        if self.status != NodeActorStatus.IDLE:
            raise create_error(f"Cannot initialize actor in status {self.status}", self)

        self.status = NodeActorStatus.INITIALIZING

        try:
            # TODO: make public method in BaseNode
            if not self.node._compiled:
                self.node.compile()

            self._validate_requirements()
            self.status = NodeActorStatus.READY

        except Exception as e:
            self.error = create_error(f"Failed to initialize actor: {e}", self)
            raise self.error from e

    def execute(
        self,
        input_: Any,
        context: dict[str, Any] | None = None,
        execution_id: UUID | None = None,
    ) -> Output[Any]:
        """
        Execute the wrapped node with the provided inputs.

        Args:
            input_: Input for the node
            context: Additional execution context
            execution_id: Optional execution tracking ID

        Returns:
            Output from node execution

        Raises:
            NodeActorError: If execution fails or actor is in invalid state
        """
        if self.status not in (NodeActorStatus.READY, NodeActorStatus.COMPLETED):
            raise create_error(f"Cannot execute actor in status {self.status}", self)

        if self._shutdown_event.is_set():
            raise create_error("Actor is shutting down", self)

        execution_id = execution_id or uuid4()
        context = context or {}

        with self._execution_lock:
            return self._execute_internal(input_, context, execution_id)

    def shutdown(self) -> None:
        """Gracefully shutdown the actor"""
        self._shutdown_event.set()
        self.status = NodeActorStatus.SHUTDOWN

        if self._execution_lock.locked():
            with self._execution_lock:
                ...

    def _execute_internal(
        self, inputs: Sequence[BaseMessage], context: dict[str, Any], execution_id: UUID
    ) -> Output[Any]:
        self.status = NodeActorStatus.EXECUTING

        try:
            execution_context = self._prepare_execution_context(context, execution_id)

            if self.node.is_llm_node:
                result = self._execute_llm_node(inputs, execution_context)
            elif self.node.is_tool_node:
                result = self._execute_tool_node(execution_context)
            else:
                result = self._execute_generic_node(inputs, execution_context)

            self.status = NodeActorStatus.COMPLETED
            return result

        except Exception as e:
            self.error = create_error(
                f"Node execution failed: {e}", self, execution_id=execution_id
            )
            raise self.error from e

    def _execute_llm_node(
        self, inputs: Sequence[BaseMessage], context: dict[str, Any]
    ) -> Output[Any]:
        if not self.llm:
            raise create_error(
                "LLM required for LLMNode execution but not provided", self
            )
        if not isinstance(self.node, LLMNode):
            raise create_error(f"Expected LLMNode, got {type(self.node)}", self)

        return self.node.invoke(self.llm, inputs, **context)

    def _execute_tool_node(self, tool_call: dict[str, Any]) -> Output[Any]:
        if not isinstance(self.node, ToolNode):
            raise create_error(f"Expected ToolNode, got {type(self.node)}", self)

        return self.node.invoke(tool_call)

    def _execute_generic_node(
        self, inputs: Sequence[BaseMessage], context: dict[str, Any]
    ) -> Output[Any]:
        if not isinstance(self.node, Node):
            raise create_error(f"Expected Node, got {type(self.node)}", self)

        return self.node.invoke(inputs, **context)

    def _validate_requirements(self) -> None:
        """
        Validate that actor has everything needed for execution
        """
        if self.node.is_llm_node and not self.llm:
            raise create_error("LLMNode requires LLM but none provided", self)

        # TODO: make public method in BaseNode
        if not self.node._compiled:
            raise create_error("Node is not compiled", self)
