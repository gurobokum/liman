import asyncio
import sys
import threading
from abc import ABC, abstractmethod
from collections.abc import Coroutine, Sequence
from typing import Any
from uuid import UUID, uuid4

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

from liman_core.base import BaseNode, Output
from liman_core.llm_node.node import LLMNode
from liman_core.node.node import Node
from liman_core.node_actor.errors import NodeActorError
from liman_core.node_actor.schemas import NodeActorState
from liman_core.tool_node.node import ToolNode
from liman_core.utils import to_snake_case

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


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

        self.state = NodeActorState.IDLE
        self.error: NodeActorError | None = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, node={self.node.name}, state={self.state})"

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
            "state": self.state,
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

        if self.llm and "llm" not in execution_context:
            execution_context["llm"] = self.llm

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
        inputs: list[BaseMessage],
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


class AsyncNodeActor(BaseNodeActor):
    """
    Async implementation of NodeActor
    """

    def __init__(
        self,
        node: BaseNode[Any],
        actor_id: UUID | None = None,
        llm: BaseChatModel | None = None,
    ):
        super().__init__(node, actor_id, llm)
        self._execution_lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()

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

    async def initialize(self) -> None:
        """
        Initialize the actor and prepare for execution
        """
        if self.state != NodeActorState.IDLE:
            raise create_error(f"Cannot initialize actor in state {self.state}", self)

        self.state = NodeActorState.INITIALIZING

        try:
            # Compile the node if not already compiled
            # TODO: make public method in BaseNode
            if not self.node._compiled:
                self.node.compile()

            await self._validate_requirements()
            self.state = NodeActorState.READY

        except Exception as e:
            self.error = create_error(f"Failed to initialize actor: {e}", self)
            raise self.error from e

    async def execute(
        self,
        inputs: Sequence[BaseMessage],
        context: dict[str, Any] | None = None,
        execution_id: UUID | None = None,
    ) -> Output[Any]:
        """
        Execute the wrapped node with the provided inputs.

        Args:
            inputs: Input messages for the node
            context: Additional execution context
            execution_id: Optional execution tracking ID

        Returns:
            Output from node execution

        Raises:
            NodeActorError: If execution fails or actor is in invalid state
        """
        if self.state not in (NodeActorState.READY, NodeActorState.COMPLETED):
            raise create_error(f"Cannot execute actor in state {self.state}", self)

        if self._shutdown_event.is_set():
            raise create_error("Actor is shutting down", self)

        execution_id = execution_id or uuid4()
        context = context or {}

        # Ensure single execution at a time
        async with self._execution_lock:
            return await self._execute_internal(inputs, context, execution_id)

    async def shutdown(self) -> None:
        """Gracefully shutdown the actor"""
        self._shutdown_event.set()
        self.state = NodeActorState.SHUTDOWN

        # Wait for any ongoing execution to complete
        if self._execution_lock.locked():
            async with self._execution_lock:
                ...

    def get_status(self) -> dict[str, Any]:
        """Get current actor status"""
        return {
            "actor_id": str(self.id),
            "node_name": self.node.name,
            "node_type": self.node.spec.kind,
            "state": self.state,
            "is_shutdown": self._shutdown_event.is_set(),
        }

    async def _execute_internal(
        self, inputs: Sequence[BaseMessage], context: dict[str, Any], execution_id: UUID
    ) -> Output[Any]:
        self.state = NodeActorState.EXECUTING

        try:
            execution_context = self._prepare_execution_context(context, execution_id)

            if self.node.is_llm_node:
                result = await self._execute_llm_node(inputs, execution_context)
            elif self.node.is_tool_node:
                result = await self._execute_tool_node(execution_context)
            else:
                result = await self._execute_generic_node(inputs, execution_context)

            self.state = NodeActorState.COMPLETED
            return result

        except Exception as e:
            self.error = create_error(
                f"Node execution failed: {e}", self, execution_id=execution_id
            )
            raise self.error from e

    async def _execute_llm_node(
        self, inputs: Sequence[BaseMessage], context: dict[str, Any]
    ) -> Output[Any]:
        if not self.llm:
            raise create_error(
                "LLM required for LLMNode execution but not provided", self
            )
        if not isinstance(self.node, LLMNode):
            raise create_error(f"Expected LLMNode, got {type(self.node)}", self)

        return await self.node.ainvoke(self.llm, inputs, **context)

    async def _execute_tool_node(self, context: dict[str, Any]) -> Any:
        if not isinstance(self.node, ToolNode):
            raise create_error(f"Expected ToolNode, got {type(self.node)}", self)

        return await self.node.ainvoke(**context)

    async def _execute_generic_node(
        self, inputs: Sequence[BaseMessage], context: dict[str, Any]
    ) -> Output[Any]:
        if not isinstance(self.node, Node):
            raise create_error(f"Expected Node, got {type(self.node)}", self)

        return await self.node.ainvoke(inputs, **context)

    def _prepare_execution_context(
        self, context: dict[str, Any], execution_id: UUID
    ) -> dict[str, Any]:
        """Prepare execution context with actor metadata"""
        execution_context = {
            **context,
            "actor_id": self.id,
            "execution_id": execution_id,
            "node_name": self.node.name,
            "node_type": self.node.spec.kind,
        }

        # Add LLM if available and not already in context
        if self.llm and "llm" not in execution_context:
            execution_context["llm"] = self.llm

        return execution_context

    async def _validate_requirements(self) -> None:
        """
        Validate that actor has everything needed for execution
        """

        # Check if LLMNode has LLM
        if self.node.is_llm_node and not self.llm:
            raise create_error("LLMNode requires LLM but none provided", self)

        # Check if node is compiled
        # TODO: make public method in BaseNode
        if not self.node._compiled:
            raise create_error("Node is not compiled", self)

        # Additional validation can be added here
        # - Authorization checks
        # - Resource availability
        # - Dependencies


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
        if self.state != NodeActorState.IDLE:
            raise create_error(f"Cannot initialize actor in state {self.state}", self)

        self.state = NodeActorState.INITIALIZING

        try:
            # TODO: make public method in BaseNode
            if not self.node._compiled:
                self.node.compile()

            self._validate_requirements()
            self.state = NodeActorState.READY

        except Exception as e:
            self.error = create_error(f"Failed to initialize actor: {e}", self)
            raise self.error from e

    def execute(
        self,
        inputs: Sequence[BaseMessage],
        context: dict[str, Any] | None = None,
        execution_id: UUID | None = None,
    ) -> Output[Any]:
        """
        Execute the wrapped node with the provided inputs.

        Args:
            inputs: Input messages for the node
            context: Additional execution context
            execution_id: Optional execution tracking ID

        Returns:
            Output from node execution

        Raises:
            NodeActorError: If execution fails or actor is in invalid state
        """
        if self.state not in (NodeActorState.READY, NodeActorState.COMPLETED):
            raise create_error(f"Cannot execute actor in state {self.state}", self)

        if self._shutdown_event.is_set():
            raise create_error("Actor is shutting down", self)

        execution_id = execution_id or uuid4()
        context = context or {}

        with self._execution_lock:
            return self._execute_internal(inputs, context, execution_id)

    def shutdown(self) -> None:
        """Gracefully shutdown the actor"""
        self._shutdown_event.set()
        self.state = NodeActorState.SHUTDOWN

        if self._execution_lock.locked():
            with self._execution_lock:
                ...

    def _execute_internal(
        self, inputs: Sequence[BaseMessage], context: dict[str, Any], execution_id: UUID
    ) -> Output[Any]:
        self.state = NodeActorState.EXECUTING

        try:
            execution_context = self._prepare_execution_context(context, execution_id)

            if self.node.is_llm_node:
                result = self._execute_llm_node(inputs, execution_context)
            elif self.node.is_tool_node:
                result = self._execute_tool_node(execution_context)
            else:
                result = self._execute_generic_node(inputs, execution_context)

            self.state = NodeActorState.COMPLETED
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

    def _execute_tool_node(self, context: dict[str, Any]) -> Any:
        if not isinstance(self.node, ToolNode):
            raise create_error(f"Expected ToolNode, got {type(self.node)}", self)

        return self.node.invoke(**context)

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
