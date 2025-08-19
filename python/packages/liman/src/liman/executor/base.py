from __future__ import annotations

import asyncio
import logging
from asyncio import Queue, Task
from typing import Any, TypeVar
from uuid import UUID, uuid4

from langchain_core.language_models.chat_models import BaseChatModel
from liman_core.base.schemas import S
from liman_core.node_actor.actor import NodeActor
from liman_core.node_actor.schemas import NextNode
from liman_core.nodes.base.node import BaseNode
from liman_core.nodes.base.schemas import NS
from liman_core.registry import Registry

from liman.conf import settings
from liman.executor.schemas import ExecutorInput, ExecutorOutput, ExecutorStatus
from liman.state import StateStorage

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
        handler.setFormatter(logging.Formatter("%(execution_id)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)


class Executor:
    def __init__(
        self,
        registry: Registry,
        state_storage: StateStorage,
        node_actor: NodeActor[T],
        llm: BaseChatModel,
        *,
        execution_id: UUID | None = None,
        max_iterations: int = 10,
        # executors
        parent_executor: Executor | None = None,
        root_output_queue: Queue[ExecutorOutput] | None = None,
    ) -> None:
        self.id = uuid4()
        self.execution_id = execution_id or uuid4()
        self.max_iterations = max_iterations

        self.registry = registry
        self.state_storage = state_storage
        self.llm = llm
        self.node_actor = node_actor

        self.status = ExecutorStatus.IDLE
        self.iteration_count = 0

        # Parent-child relationship
        self.parent_executor = parent_executor

        # Child management
        self.child_executors: dict[UUID, Executor] = {}

        # Queues for input and output management
        self._input_queue: Queue[ExecutorInput] = Queue()
        self._output_queue: Queue[ExecutorOutput] = Queue()
        self._root_output_queue: Queue[ExecutorOutput] = root_output_queue or Queue()
        self._processing_task: Task[None] | None = None

        self.logger = logging.LoggerAdapter(
            logger, {"execution_id": str(self.execution_id)}
        )

        self.logger.debug("Created executor")

    @property
    def is_child(self) -> bool:
        """
        Check if the current executor is a child executor
        """
        return self.parent_executor is not None

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

    async def _process_input_loop(self) -> None:
        try:
            while self.status != ExecutorStatus.COMPLETED:
                self.logger.debug(f"Iteration: {self.iteration_count}")
                if self.iteration_count >= self.max_iterations:
                    raise RuntimeError(
                        f"Executor exceeded max iterations ({self.max_iterations})"
                    )

                input_ = await self._input_queue.get()
                self.logger.debug(f"Executor getting input from queue: {repr(input_)}")
                self.iteration_count += 1

                if input_.execution_id != self.execution_id:
                    child_executor = self.child_executors[input_.execution_id]
                    self.logger.debug(
                        f"Executor delegates input to child executor {child_executor.execution_id}"
                    )
                    asyncio.create_task(child_executor.step(input_))
                    continue

                self.logger.debug(
                    f"Executor executes node {input_.node_full_name} with input {repr(input_)}"
                )
                result = await self._execute_node(input_)

                if not result.next_nodes:
                    output = ExecutorOutput(
                        execution_id=self.execution_id,
                        node_actor_id=self.node_actor.id,
                        node_full_name=self.node_actor.node.full_name,
                        node_output=result.output,
                        exit_=True,
                    )
                    self.logger.debug(
                        f"Executor completed with output: {repr(output)}, queue size: {self._output_queue.qsize()}"
                    )
                    await self._output_queue.put(output)
                    self.status = ExecutorStatus.COMPLETED
                    break

                self.logger.debug(f"Next nodes to process: {result.next_nodes}")
                await self._handle_next_nodes(input_, result)
        except Exception as e:
            self.logger.exception(f"Executor fails with {e}")
            self.status = ExecutorStatus.FAILED
            error_output = ExecutorOutput(
                execution_id=self.execution_id,
                node_full_name=self.node_actor.node.full_name,
                node_actor_id=self.node_actor.id,
                node_output=None,
                exit_=True,
            )
            await self._output_queue.put(error_output)
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

    async def _execute_node(self, input_: ExecutorInput) -> Any:
        """
        Execute the node with the given input

        Args:
            input_: ExecutorInput containing current input and target
        """

        self.status = ExecutorStatus.RUNNING
        # Get node actor

        node_input = input_.node_input
        result = await self.node_actor.execute(
            node_input, execution_id=self.execution_id
        )

        # Save state after execution
        actor_state = self.node_actor.serialize_state()
        await self.state_storage.asave_actor_state(
            input_.execution_id, self.node_actor.id, actor_state
        )

        return result

    async def _handle_next_nodes(self, input_: ExecutorInput, result: Any) -> None:
        """
        Handle the next nodes based on the execution result

        Args:
            result: Result of the node execution
            input_: ExecutorInput containing current input and target
        """
        next_nodes = result.next_nodes

        if len(next_nodes) == 1:
            await self._handle_sequential_execution(next_nodes[0])
        else:
            await self._handle_parallel_execution(next_nodes)

    async def _handle_sequential_execution(self, next_node_tuple: NextNode) -> None:
        """
        Handle sequential execution of the next node
        """
        self.logger.debug(
            "Sequential execution with next node tuple: %s", next_node_tuple
        )
        next_node, node_input = next_node_tuple
        child_executor = await self._fork_executor(next_node)

        child_input = ExecutorInput(
            execution_id=child_executor.execution_id,
            node_actor_id=child_executor.node_actor.id,
            node_input=node_input,
            node_full_name=next_node.full_name,
        )

        # Execute child and get result
        child_output = await child_executor.step(child_input)

        continue_input = ExecutorInput(
            execution_id=self.execution_id,
            node_actor_id=self.node_actor.id,
            node_input=child_output.node_output,
            node_full_name=self.node_actor.node.full_name,
        )

        await self._input_queue.put(continue_input)

    async def _handle_parallel_execution(
        self,
        next_nodes: list[NextNode],
    ) -> None:
        """
        Handle parallel execution of multiple nodes
        """
        self.status = ExecutorStatus.SUSPENDED

        async def _handle_next_node(next_node_tuple: NextNode) -> ExecutorOutput:
            next_node, node_input = next_node_tuple
            child_executor = await self._fork_executor(next_node)
            child_input = ExecutorInput(
                execution_id=child_executor.execution_id,
                node_actor_id=child_executor.node_actor.id,
                node_input=node_input,
                node_full_name=next_node.full_name,
            )
            return await child_executor.step(child_input)

        child_outputs = await asyncio.gather(
            *[_handle_next_node(next_node) for next_node in next_nodes]
        )

        self.status = ExecutorStatus.RUNNING
        if child_outputs:
            combined_input = ExecutorInput(
                execution_id=self.execution_id,
                node_actor_id=self.node_actor.id,
                node_input=[output.node_output for output in child_outputs],
                node_full_name=self.node_actor.node.full_name,
            )
            await self._input_queue.put(combined_input)

    async def _fork_executor(self, node: BaseNode[S, NS]) -> Executor:
        """
        Create child executor for the given node
        """
        child_node_actor = NodeActor.create(node, llm=self.llm)

        child_executor = Executor(
            registry=self.registry,
            state_storage=self.state_storage,
            node_actor=child_node_actor,
            llm=self.llm,
            parent_executor=self,
            root_output_queue=self._root_output_queue,
        )
        self.logger.debug(
            f"Executor forks executor with id {child_executor.execution_id} for node {node.full_name}"
        )

        self.child_executors[child_executor.execution_id] = child_executor
        return child_executor
