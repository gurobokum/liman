import asyncio
import sys
import threading
from collections.abc import Sequence
from typing import Any, TypedDict
from uuid import UUID, uuid4

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

from liman_core.base.node import BaseNode, Output
from liman_core.llm_node.node import LLMNode
from liman_core.node.node import Node
from liman_core.node_actor.errors import NodeActorError
from liman_core.node_actor.schemas import NodeActorStatus
from liman_core.plugins.core.base import ExecutionStateProvider
from liman_core.tool_node.node import ToolNode
from liman_core.utils import to_snake_case

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class State(TypedDict):
    messages: list[BaseMessage]


class NodeActor:
    """
    Unified NodeActor supporting both sync and async execution
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

        self._execution_lock = threading.Lock()
        self._async_execution_lock = asyncio.Lock()
        self._shutdown_event = threading.Event()
        self._async_shutdown_event = asyncio.Event()
        self._state: State = {"messages": []}

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

    def _is_async_shutdown(self) -> bool:
        """Check if actor is shutdown (async version)"""
        return self._async_shutdown_event.is_set()

    def initialize(self) -> None:
        """
        Initialize the actor and prepare for execution
        """
        if self.status != NodeActorStatus.IDLE:
            raise create_error(f"Cannot initialize actor in status {self.status}", self)

        self.status = NodeActorStatus.INITIALIZING

        try:
            if not self.node._compiled:
                self.node.compile()

            self._validate_requirements()
            self.status = NodeActorStatus.READY

        except Exception as e:
            self.error = create_error(f"Failed to initialize actor: {e}", self)
            raise self.error from e

    async def ainitialize(self) -> None:
        """
        Initialize the actor and prepare for execution (async version)
        """
        if self.status != NodeActorStatus.IDLE:
            raise create_error(f"Cannot initialize actor in status {self.status}", self)

        self.status = NodeActorStatus.INITIALIZING

        try:
            if not self.node._compiled:
                self.node.compile()

            await self._avalidate_requirements()
            self.status = NodeActorStatus.READY

        except Exception as e:
            self.error = create_error(f"Failed to initialize actor: {e}", self)
            raise self.error from e

    def execute(
        self,
        input_: Any,
        execution_id: UUID,
        context: dict[str, Any] | None = None,
    ) -> Output:
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

        context = context or {}

        with self._execution_lock:
            return self._execute_internal(input_, context, execution_id)

    async def aexecute(
        self,
        input_: Any,
        execution_id: UUID,
        context: dict[str, Any] | None = None,
    ) -> Output:
        """
        Execute the wrapped node with the provided inputs (async version).

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

        if self._async_shutdown_event.is_set():
            raise create_error("Actor is shutting down", self)

        execution_id = execution_id or uuid4()
        context = context or {}

        async with self._async_execution_lock:
            return await self._aexecute_internal(input_, context, execution_id)

    def shutdown(self) -> None:
        """Gracefully shutdown the actor"""
        self._shutdown_event.set()
        self.status = NodeActorStatus.SHUTDOWN

        if self._execution_lock.locked():
            with self._execution_lock:
                ...

    async def ashutdown(self) -> None:
        """Gracefully shutdown the actor (async version)"""
        self._async_shutdown_event.set()
        self.status = NodeActorStatus.SHUTDOWN

        if self._async_execution_lock.locked():
            async with self._async_execution_lock:
                ...

    def get_status(self) -> dict[str, Any]:
        """Get current actor status"""
        return {
            "actor_id": str(self.id),
            "node_name": self.node.name,
            "node_type": self.node.spec.kind,
            "status": self.status,
            "is_shutdown": self._is_shutdown(),
        }

    def _execute_internal(
        self, inputs: Sequence[BaseMessage], context: dict[str, Any], execution_id: UUID
    ) -> Output:
        self.status = NodeActorStatus.EXECUTING

        registry = self.node.registry
        plugins = [
            plugin
            for plugin in registry.get_plugins(self.node.spec.kind)
            if isinstance(plugin, ExecutionStateProvider)
        ]
        state = {
            k: v
            for d in [
                plugin.get_execution_state(self.node, context, registry)
                for plugin in plugins
            ]
            for k, v in d.items()
        }

        try:
            execution_context = self._prepare_execution_context(context, execution_id)

            if self.node.is_llm_node:
                result = self._execute_llm_node(inputs, state, execution_context)
            elif self.node.is_tool_node:
                result = self._execute_tool_node(state, execution_context)
            else:
                result = self._execute_generic_node(inputs, state, execution_context)

            self.status = NodeActorStatus.COMPLETED
            return result

        except Exception as e:
            self.error = create_error(
                f"Node execution failed: {e}", self, execution_id=execution_id
            )
            raise self.error from e

    async def _aexecute_internal(
        self, input_: Any, context: dict[str, Any], execution_id: UUID
    ) -> Output:
        self.status = NodeActorStatus.EXECUTING

        try:
            execution_context = self._prepare_execution_context(context, execution_id)

            if self.node.is_llm_node:
                result = await self._aexecute_llm_node(input_, execution_context)
                self._state["messages"].append(result.response)
            elif self.node.is_tool_node:
                result = await self._aexecute_tool_node(input_)
            else:
                result = await self._aexecute_generic_node(input_, execution_context)

            self.status = NodeActorStatus.COMPLETED
            return result

        except Exception as e:
            self.error = create_error(
                f"Node execution failed: {e}", self, execution_id=execution_id
            )
            raise self.error from e

    def _execute_llm_node(
        self,
        inputs: Sequence[BaseMessage],
        state: dict[str, Any],
        context: dict[str, Any],
    ) -> Output:
        if not self.llm:
            raise create_error(
                "LLM required for LLMNode execution but not provided", self
            )
        if not isinstance(self.node, LLMNode):
            raise create_error(f"Expected LLMNode, got {type(self.node)}", self)

        return self.node.invoke(self.llm, inputs, state, **context)

    async def _aexecute_llm_node(
        self, input_: BaseMessage, context: dict[str, Any]
    ) -> Output:
        if not self.llm:
            raise create_error(
                "LLM required for LLMNode execution but not provided", self
            )

        self._state["messages"].append(input_)
        return await self.node.ainvoke(self.llm, self._state["messages"], **context)

    def _execute_tool_node(
        self, tool_call: dict[str, Any], state: dict[str, Any]
    ) -> Output:
        if not isinstance(self.node, ToolNode):
            raise create_error(f"Expected ToolNode, got {type(self.node)}", self)

        return self.node.invoke(tool_call, state)

    async def _aexecute_tool_node(
        self, tool_call: dict[str, Any], state: dict[str, Any] | None = None
    ) -> Output:
        if not isinstance(self.node, ToolNode):
            raise create_error(f"Expected ToolNode, got {type(self.node)}", self)

        return await self.node.ainvoke(tool_call, state=state)

    def _execute_generic_node(
        self,
        inputs: Sequence[BaseMessage],
        state: dict[str, Any],
        context: dict[str, Any],
    ) -> Output:
        if not isinstance(self.node, Node):
            raise create_error(f"Expected Node, got {type(self.node)}", self)

        return self.node.invoke(inputs, state, **context)

    async def _aexecute_generic_node(
        self, inputs: Sequence[BaseMessage], context: dict[str, Any]
    ) -> Output:
        if not isinstance(self.node, Node):
            raise create_error(f"Expected Node, got {type(self.node)}", self)

        return await self.node.ainvoke(inputs, **context)

    def _validate_requirements(self) -> None:
        """
        Validate that actor has everything needed for execution
        """
        if self.node.is_llm_node and not self.llm:
            raise create_error("LLMNode requires LLM but none provided", self)

        if not self.node._compiled:
            raise create_error("Node is not compiled", self)

    async def _avalidate_requirements(self) -> None:
        """
        Validate that actor has everything needed for execution (async version)
        """
        if self.node.is_llm_node and not self.llm:
            raise create_error("LLMNode requires LLM but none provided", self)

        if not self.node._compiled:
            raise create_error("Node is not compiled", self)

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


def create_error(
    message: str, actor: NodeActor, *, execution_id: UUID | None = None
) -> NodeActorError:
    return NodeActorError(
        message,
        actor_id=actor.id,
        actor_composite_id=actor.composite_id,
        node_kind=actor.node.spec.kind,
        node_name=actor.node.name,
        execution_id=execution_id,
    )
