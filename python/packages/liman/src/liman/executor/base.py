from __future__ import annotations

import asyncio
import logging
import sys
from asyncio import Queue, Task
from dataclasses import dataclass
from typing import Any, NamedTuple, TypeVar
from uuid import UUID, uuid4

from langchain_core.language_models.chat_models import BaseChatModel
from liman_core.base.schemas import S
from liman_core.errors import LimanError
from liman_core.node_actor.actor import NodeActor
from liman_core.node_actor.schemas import NextNode, Result
from liman_core.nodes.base.node import BaseNode
from liman_core.nodes.base.schemas import NS
from liman_core.nodes.supported_types import get_node_cls
from liman_core.registry import Registry
from pydantic import ValidationError

from liman.conf import settings
from liman.executor.errors import ExecutorRestoreError
from liman.executor.schemas import (
    ExecutorInput,
    ExecutorOutput,
    ExecutorState,
    ExecutorStatus,
)
from liman.state import StateStorage

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseNode[Any, Any])

if settings.DEBUG:
    try:
        from rich.logging import RichHandler
    except ImportError:
        logger.warning(
            "Rich logging is not available. Install 'rich' package to enable rich logging."
        )
    else:
        handler = RichHandler(show_time=True, show_path=True, rich_tracebacks=True)
        handler.setFormatter(logging.Formatter("%(executor_id)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)


@dataclass
class LazyExecutor:
    id: UUID


class ParentExecutorPair(NamedTuple):
    parent_executor: LazyExecutor | Executor
    node_actor_id: UUID


class Executor:
    node_actors: dict[UUID, NodeActor[Any]]
    parent_executor_pair: ParentExecutorPair | None
    child_executors: dict[UUID, LazyExecutor | Executor]

    def __init__(
        self,
        registry: Registry,
        state_storage: StateStorage,
        llm: BaseChatModel,
        *,
        executor_id: UUID | None = None,
        execution_id: UUID | None = None,
        iteration_count: int = 0,
        max_iterations: int = 10,
        # executors
        parent_executor_pair: ParentExecutorPair | None = None,
        # root_output_queue: Queue[ExecutorOutput] | None = None,
        child_executors: set[UUID] | None = None,
    ) -> None:
        self.id = executor_id or uuid4()
        self.execution_id = execution_id or uuid4()
        self.max_iterations = max_iterations

        self.registry = registry
        self.state_storage = state_storage
        self.llm = llm

        self.status = ExecutorStatus.IDLE
        self.iteration_count = iteration_count

        # NodeActors
        self.node_actors = {}

        # Parent-child relationship
        self.parent_executor_pair = parent_executor_pair
        self.child_executors = (
            {id_: LazyExecutor(id=id_) for id_ in child_executors}
            if child_executors
            else {}
        )

        # Queues for input and output management
        self._input_queue: Queue[ExecutorInput] = Queue()
        self._output_queue: Queue[ExecutorOutput] = Queue()
        self._processing_task: Task[None] | None = None
        self._output: ExecutorOutput | None = None

        self.logger = logging.LoggerAdapter(logger, {"executor_id": str(self.id)})

        self.logger.debug("Created executor")

    @property
    def is_child(self) -> bool:
        """
        Check if the current executor is a child executor
        """
        return self.parent_executor_pair is not None

    @classmethod
    async def restore(
        cls,
        registry: Registry,
        state_storage: StateStorage,
        llm: BaseChatModel,
        executor_id: UUID,
        execution_id: UUID | None = None,
        max_iterations: int = 10,
    ) -> Self:
        """
        Restore an executor from saved state.

        Args:
            executor_id: The unique ID of the executor to restore.
            execution_id: The unique ID of the execution trace. Optional if it can be determined from the state.
            max_iterations: The maximum number of iterations to run. Default is 10.
        """
        raw_state = None
        if executor_id:
            raw_state = await state_storage.load_executor_state(executor_id)

        parent_executor_pair = None
        if raw_state and (pair := raw_state["parent_executor_pair"]):
            parent_executor_pair = ParentExecutorPair(
                LazyExecutor(id=pair[0]),
                pair[1],
            )

        if not raw_state:
            raise ExecutorRestoreError(
                f"Executor state not found for executor_id {executor_id}"
            )

        try:
            state = ExecutorState.model_validate(raw_state)
        except ValidationError as e:
            raise ExecutorRestoreError(
                f"Improper state for executor_id {executor_id}"
            ) from e

        if state.executor_id != executor_id:
            raise ExecutorRestoreError(
                f"Executor ids do not match {state.executor_id} <> {executor_id}"
            )

        return cls(
            registry=registry,
            state_storage=state_storage,
            llm=llm,
            executor_id=executor_id,
            execution_id=execution_id,
            iteration_count=state.iteration_count,
            max_iterations=max_iterations,
            parent_executor_pair=parent_executor_pair,
        )

    @classmethod
    async def restore_or_create(
        cls,
        registry: Registry,
        state_storage: StateStorage,
        llm: BaseChatModel,
        *,
        executor_id: UUID | None = None,
        execution_id: UUID | None = None,
        max_iterations: int = 10,
    ) -> Self:
        try:
            if not executor_id:
                raise ExecutorRestoreError(
                    "executor_id is required for restoring executor"
                )

            return await cls.restore(
                registry, state_storage, llm, executor_id, execution_id, max_iterations
            )
        except ExecutorRestoreError:
            return cls(
                registry=registry,
                state_storage=state_storage,
                llm=llm,
                executor_id=executor_id,
                execution_id=execution_id,
                max_iterations=max_iterations,
            )

    async def step(self, input_: ExecutorInput) -> ExecutorOutput:
        """
        Execute a single step in the executor

        Args:
            input_: ExecutorInput containing current input and target
        """
        self.status = ExecutorStatus.RUNNING
        self.logger.debug(
            f"Executor stepping with input: {repr(input_)}, qsize: {self._input_queue.qsize()}"
        )

        await self._input_queue.put(input_)

        if not self._processing_task:
            self._processing_task = asyncio.create_task(self._process_input_loop())
            self._processing_task.add_done_callback(self._on_exit_input_loop)

        res = await self._output_queue.get()
        return res

    async def check_childs(self) -> None:
        self.logger.debug(f"Rechecking childs for the output {self.id}")

        if self.status != ExecutorStatus.SUSPENDED:
            raise RuntimeError(f"Executor has improper status {self.id} {self.status}")

        output = []

        for child_ in self.child_executors.values():
            if isinstance(child_, Executor):
                child_executor = child_
            else:
                child_executor = await Executor.restore_or_create(
                    self.registry,
                    self.state_storage,
                    self.llm,
                    executor_id=child_.id,
                    execution_id=self.execution_id,
                    max_iterations=self.max_iterations,
                )
                self.child_executors[child_executor.id] = child_executor

            if child_executor.status not in (
                ExecutorStatus.COMPLETED,
                ExecutorStatus.FAILED,
            ):
                # Wait until all child processes are ready
                break
            output.append(await child_executor.get_output())

        def _get_node_output(output: ExecutorOutput | BaseException) -> Any:
            if isinstance(output, BaseException):
                return str(output)
            return output.node_output

        raw_state = await self.state_storage.load_executor_state(self.id)
        if not raw_state:
            raise LimanError(
                f"Parent executor state is missed, it could not be restored properly {self.id}"
            )
        node_actor_id = raw_state["node_actor_id"]
        raw_actor_state = await self.state_storage.load_actor_state(
            self.id, node_actor_id
        )
        if not raw_actor_state:
            raise LimanError(
                f"Node actor state is missed, parent executor cannot buld properly restored {self.id} {node_actor_id}"
            )

        self.status = ExecutorStatus.IDLE
        await self.state_storage.save_executor_state(
            self.id, self.serialize_state(node_actor_id)
        )

        input_ = ExecutorInput(
            executor_id=self.id,
            execution_id=self.execution_id,
            node_actor_id=node_actor_id,
            node_input=[_get_node_output(o) for o in output],
            node_fullname=raw_actor_state["node_fullname"],
            # TODO: reconsider how to restore the context
            # context=context,
        )
        await self._input_queue.put(input_)

    def serialize_state(self, node_actor_id: UUID) -> dict[str, Any]:
        return ExecutorState(
            executor_id=self.id,
            node_actor_id=node_actor_id,
            execution_id=self.execution_id,
            status=self.status,
            parent_executor_pair=(
                self.parent_executor_pair[0].id,
                self.parent_executor_pair[1],
            )
            if self.parent_executor_pair
            else None,
            child_executor_ids=set(self.child_executors.keys()),
            iteration_count=self.iteration_count,
        ).model_dump()

    async def get_output(self) -> ExecutorOutput:
        if self.status not in (ExecutorStatus.COMPLETED, ExecutorStatus.FAILED):
            raise RuntimeError(
                f"Cannot retrieve output for executor having {self.status} status"
            )

        if self._output:
            return self._output

        # Restore output
        raw_state = await self.state_storage.load_executor_state(self.id)
        state = ExecutorState.model_validate(raw_state)

        raw_actor_state = await self.state_storage.load_actor_state(
            self.id, state.node_actor_id
        )
        if not raw_actor_state:
            raise RuntimeError(
                f"Invalid executor state - it is stopped but does not have actor state {self.id}"
            )

        # TODO: drop node_fullname
        node_actor = await self._get_or_create_node_actor(
            state.node_actor_id, raw_actor_state["node_fullname"]
        )

        self._output = ExecutorOutput(
            executor_id=self.id,
            execution_id=self.execution_id,
            node_actor_id=node_actor.id,
            node_fullname=node_actor.node.full_name,
            node_output=node_actor.node.output,
            exit_=True,
        )
        return self._output

    async def _process_input_loop(self) -> None:
        try:
            while self.status not in (ExecutorStatus.COMPLETED, ExecutorStatus.FAILED):
                self.logger.debug("Executor iteration=%d", self.iteration_count)

                input_ = await self._input_queue.get()
                self.logger.debug(f"Executor getting input from queue: {repr(input_)}")

                if input_.executor_id != self.id:
                    raise RuntimeError(
                        f"Wrong executor received the input {self.id} when expected {input_.executor_id}"
                    )

                self.logger.debug(
                    "Executor executes node %s with input %s",
                    input_.node_fullname,
                    repr(input_),
                )

                try:
                    # TODO: move iteration_count check to the top
                    if self.iteration_count >= self.max_iterations:
                        raise RuntimeError(
                            f"Executor exceeded max iterations ({self.max_iterations})"
                        )
                    self.iteration_count += 1
                    result, node_actor = await self._execute(input_)
                except Exception:
                    self.status = ExecutorStatus.FAILED
                    error_output = ExecutorOutput(
                        executor_id=self.id,
                        execution_id=self.execution_id,
                        # TODO: pass proper node_actor_id if possible
                        node_actor_id=input_.node_actor_id or uuid4(),
                        node_fullname=input_.node_fullname,
                        node_output=None,
                        exit_=True,
                    )
                    self._output = error_output
                    # TODO: do we really need output queue
                    await self._output_queue.put(error_output)
                    await self._send_output_to_parent(error_output)
                    raise

                self.logger.debug(f"Next nodes to process: {result.next_nodes}")
                await self._handle_next_nodes(input_, result, node_actor)
        except Exception as e:
            self.logger.exception(f"Executor fails with {e}")
            raise
        finally:
            self._processing_task = None

    def _on_exit_input_loop(self, task: Task[None]) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            ...
        except Exception:
            raise
        finally:
            self.logger.debug("Executor stopped processing input loop")
            self._processing_task = None

    async def _execute(self, input_: ExecutorInput) -> tuple[Result, NodeActor[Any]]:
        """
        Run the node with the given input.
        Restore the NodeActor if it exists, or create a new one.

        Args:
            input_: ExecutorInput containing the current input and target.
        """
        if self.id != input_.executor_id:
            # TODO add specific error
            raise LimanError("Executor_id doesn't match of the input_.executor_id")

        self.status = ExecutorStatus.RUNNING

        node_actor = await self._get_or_create_node_actor(
            input_.node_actor_id, input_.node_fullname
        )

        # Save state before execution
        # TODO: add single method for strong consistency
        await self.state_storage.save_actor_state(
            self.id, node_actor.id, node_actor.serialize_state()
        )
        await self.state_storage.save_executor_state(
            self.id, self.serialize_state(node_actor.id)
        )

        node_input = input_.node_input
        result = await node_actor.execute(
            node_input, execution_id=self.execution_id, context=input_.context
        )

        self.status = ExecutorStatus.IDLE

        # Save state after execution
        # TODO: add single method for strong consistency
        await self.state_storage.save_actor_state(
            self.id, node_actor.id, node_actor.serialize_state()
        )
        await self.state_storage.save_executor_state(
            self.id, self.serialize_state(node_actor.id)
        )

        return result, node_actor

    async def _get_or_create_node_actor(
        self, node_actor_id: UUID | None, node_fullname: str
    ) -> NodeActor[Any]:
        """
        Try to restore an existing node actor from the state; if not found, create a new one.
        """
        raw_actor_state = None

        if node_actor_id:
            if node_actor := self.node_actors.get(node_actor_id):
                return node_actor

            raw_actor_state = await self.state_storage.load_actor_state(
                self.id, node_actor_id
            )

        node_cls, node_name = node_fullname.split("/")
        node = self.registry.lookup(get_node_cls(node_cls), node_name)

        node_actor = await NodeActor.restore_or_create(
            node, llm=self.llm, state=raw_actor_state
        )
        self.node_actors[node_actor.id] = node_actor
        return node_actor

    async def _handle_next_nodes(
        self, input_: ExecutorInput, result: Result, node_actor: NodeActor[Any]
    ) -> None:
        """
        Handle the next nodes based on the execution result

        Args:
            result: The output produced by executing the node.
            input_: ExecutorInput containing the current input and target information.
        """
        next_nodes = result.next_nodes

        if len(next_nodes) == 0:
            # Complete execution
            await self._handle_complete_execution(result, node_actor)
        elif len(next_nodes) == 1:
            # Sequenital execution
            await self._handle_sequential_execution(
                next_nodes[0], context=input_.context
            )
        else:
            # Fan-Out
            await self._handle_parallel_execution(
                next_nodes, node_actor, context=input_.context
            )

    async def _handle_complete_execution(
        self, result: Result, node_actor: NodeActor[Any]
    ) -> None:
        output = ExecutorOutput(
            executor_id=self.id,
            execution_id=self.execution_id,
            node_actor_id=node_actor.id,
            node_fullname=node_actor.node.full_name,
            node_output=result.output,
            exit_=True,
        )
        self.status = ExecutorStatus.COMPLETED
        await self.state_storage.save_executor_state(
            self.id, self.serialize_state(node_actor.id)
        )

        self._output = output
        # TODO: do we need queue?
        await self._output_queue.put(self._output)

        self.logger.debug(
            "Executor completed with output: %s, queue size: %s",
            repr(output),
            self._output_queue.qsize(),
        )
        await self._send_output_to_parent(output)

    async def _send_output_to_parent(self, output: ExecutorOutput) -> None:
        if not self.parent_executor_pair:
            return

        executor = self.parent_executor_pair[0]
        if isinstance(executor, Executor):
            parent_executor = executor
        else:
            parent_executor = await Executor.restore_or_create(
                self.registry,
                self.state_storage,
                self.llm,
                executor_id=executor.id,
                execution_id=output.execution_id,
            )
            self.parent_executor_pair = ParentExecutorPair(
                parent_executor,
                self.parent_executor_pair[1],
            )
        asyncio.create_task(parent_executor.check_childs())

    async def _handle_sequential_execution(
        self, next_node_tuple: NextNode, context: dict[str, Any] | None = None
    ) -> None:
        """
        Handle moving to the next node in a sequence.

        The executor advances to the next node_actor for sequential execution.
        """
        self.logger.debug(
            "Sequential execution with next node tuple: %s", next_node_tuple
        )
        next_node, node_input = next_node_tuple

        next_input = ExecutorInput(
            executor_id=self.id,
            execution_id=self.execution_id,
            node_actor_id=None,
            node_input=node_input,
            node_fullname=next_node.full_name,
            context=context,
        )

        await self._input_queue.put(next_input)

    async def _handle_parallel_execution(
        self,
        next_nodes: list[NextNode],
        node_actor: NodeActor[Any],
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Run multiple nodes in parallel
        """
        self.status = ExecutorStatus.SUSPENDED

        async def _handle_next_node(next_node_tuple: NextNode) -> ExecutorOutput:
            next_node, node_input = next_node_tuple
            child_executor = await self._fork_executor(next_node, node_actor)
            child_input = ExecutorInput(
                executor_id=child_executor.id,
                execution_id=child_executor.execution_id,
                node_input=node_input,
                node_fullname=next_node.full_name,
                context=context,
            )
            return await child_executor.step(child_input)

        for next_node in next_nodes:
            asyncio.create_task(_handle_next_node(next_node))

    async def _fork_executor(
        self, node: BaseNode[S, NS], node_actor: NodeActor[Any]
    ) -> Executor:
        """
        Create a child executor for the given node.
        """
        child_executor = Executor(
            registry=self.registry,
            state_storage=self.state_storage,
            llm=self.llm,
            execution_id=self.execution_id,
            max_iterations=self.max_iterations,
            parent_executor_pair=ParentExecutorPair(self, node_actor.id),
        )
        self.logger.debug(
            "Executor forks executor with id %s for node %s",
            child_executor.id,
            node.full_name,
        )

        self.child_executors[child_executor.id] = child_executor
        return child_executor
