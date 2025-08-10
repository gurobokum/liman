from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID, uuid4

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel

from liman_core.base.schemas import S
from liman_core.executor.state import ExecutorState, ExecutorStatus, StateStorage
from liman_core.node_actor.actor import NodeActor
from liman_core.node_actor.schemas import Result
from liman_core.nodes.base.node import BaseNode
from liman_core.nodes.base.schemas import NS, NodeOutput
from liman_core.nodes.supported_types import get_node_cls
from liman_core.registry import Registry


class ExecutorInput(BaseModel):
    execution_id: UUID
    node_actor_id: UUID
    node_input: Any


class ExecutorOutput(BaseModel):
    execution_id: UUID
    node_actor_id: UUID
    node_output: NodeOutput
    exit_: bool = False


class Executor:
    """
    Executor that replicates imperative agent flow with intelligent traversal,
    parallelization, and state management coordinating with NodeActor states
    """

    def __init__(
        self,
        registry: Registry,
        state_storage: StateStorage,
        node_actor: NodeActor[S, NS],
        llm: BaseChatModel,
        execution_id: UUID | None = None,
        root_executor: Executor | None = None,
        parent_executor: Executor | None = None,
    ) -> None:
        self.registry = registry
        self.state_storage = state_storage
        self.llm = llm

        self.state = ExecutorState(
            execution_id=execution_id or uuid4(),
            node_actor_id=node_actor.id,
            status=ExecutorStatus.RUNNING,
            child_executor_ids=set(),
            iteration_count=0,
        )

        self.node_actor = node_actor
        self.child_executors: dict[UUID, Executor] = {}
        self.root_executor = root_executor or self
        self.parent_executor = parent_executor

    @classmethod
    async def restore(
        cls,
        registry: Registry,
        snapshot: dict[str, dict[str, Any]],
        state_storage: StateStorage,
        llm: BaseChatModel,
        execution_id: UUID,
    ) -> Executor:
        """
        Restore executor from saved state snapshot
        """
        root_key = str(execution_id)
        if root_key not in snapshot:
            raise ValueError(f"Root executor {execution_id} not found in snapshot")

        # DFS stack for top-to-bottom restoration: (executor_key, parent_executor)
        stack: list[tuple[str, Executor | None]] = [(root_key, None)]
        restored_executors: dict[str, Executor] = {}
        root_executor: Executor | None = None

        while stack:
            executor_key, parent_executor = stack.pop()

            if executor_key in restored_executors:
                continue

            state_data = snapshot[executor_key]
            executor_state = ExecutorState.model_validate(state_data)

            # Create NodeActor
            node_actor_state = await state_storage.aload_actor_state(
                execution_id, executor_state.node_actor_id
            )
            if not node_actor_state:
                raise ValueError(
                    f"NodeActor state for {executor_state.node_actor_id} not found"
                )
            node_type = node_actor_state["node_type"]
            node_cls = get_node_cls(node_type)
            node_name = node_actor_state["node_name"]
            node = registry.lookup(node_cls, node_name)
            node_actor = await NodeActor[Any, Any].acreate_or_restore(
                node, state=node_actor_state, llm=llm
            )

            # Create executor instance
            executor = cls(
                registry=registry,
                state_storage=state_storage,
                llm=llm,
                node_actor=node_actor,
                execution_id=UUID(executor_key),
                root_executor=root_executor,
                parent_executor=parent_executor,
            )

            if not root_executor:
                # This is the root executor
                root_executor = executor

            # Restore state
            executor.state = executor_state
            executor.child_executors = {}

            restored_executors[executor_key] = executor

            # Link to root
            if root_executor:
                root_executor.child_executors[UUID(executor_key)] = executor
                root_executor.state.child_executor_ids.add(UUID(executor_key))

            # Add children to stack for processing
            for child_id in executor.state.child_executor_ids:
                stack.append((str(child_id), executor))

        return restored_executors[root_key]

    @property
    def execution_id(self) -> UUID:
        """
        Get the unique execution ID for this executor
        """
        return self.state.execution_id

    @property
    def is_child(self) -> bool:
        """
        Check if this executor is a child of another executor
        """
        return self.parent_executor is not None

    async def execute_flow(
        self, input_: ExecutorInput, max_iterations: int = 50
    ) -> AsyncGenerator[ExecutorOutput, None]:
        """
        Execute complete agent flow, yielding events as they occur

        Args:
            input_: Initial input message
            max_iterations: Max iterations to prevent infinite loops

        Yields:
            Responses from the node execution
        """

        while True:
            try:
                output = await self.step(input_, max_iterations=max_iterations)
                yield output
            except Exception as e:
                # Error handling
                raise RuntimeError(f"Execution failed: {e}") from e

    async def step(
        self, input_: ExecutorInput, max_iterations: int = 50
    ) -> ExecutorOutput:
        """
        Execute steps until output is needed or execution completes

        Args:
            input_: ExecutorInput containing current input and target
            max_iterations: Max iterations to prevent infinite loops

        Returns:
            Result object containing node output and next nodes to execute
        """

        while self.state.iteration_count < max_iterations:
            self.state.iteration_count += 1
            await self.root_executor.save_state()

            _, node_actor = self._find_target_for_input(input_)
            result = await node_actor.aexecute(
                input_.node_input, execution_id=input_.execution_id
            )
            actor_state = self.node_actor.serialize_state()
            await self.state_storage.asave_actor_state(
                input_.execution_id, node_actor.id, actor_state
            )

            # Exit the flow
            if len(result.next_nodes) == 0:
                # bubble up the result if no next nodes
                # TODO
                # await self._bubble_up_completion(result)
                return ExecutorOutput(
                    execution_id=self.execution_id,
                    node_actor_id=node_actor.id,
                    node_output=result.node_output,
                    exit_=True,
                )

            # Sequential execution - continue to next node
            if len(result.next_nodes) == 1:
                next_node, node_input = result.next_nodes[0]
                node_actor = await self._get_or_create_node_actor(input_, next_node)
                execution_id = input_.execution_id
                input_ = ExecutorInput(
                    execution_id=execution_id,
                    node_actor_id=node_actor.id,
                    node_input=node_input,
                )
                continue

            # Parallel execution - multiple next nodes
            outputs = await self._execute_parallel(result.next_nodes)
            input_ = ExecutorInput(
                execution_id=input_.execution_id,
                node_actor_id=node_actor.id,
                node_input=[output.node_output for output in outputs],
            )

        raise RuntimeError(f"Execution exceeded max iterations ({max_iterations})")

    async def handle_child_completed(self, child_execution_id: UUID) -> None:
        """
        Handle notification that a child executor has completed
        """
        self.child_executors.pop(child_execution_id)

        # Check if all children are completed and resume if needed
        if not self.child_executors and self.state.status == ExecutorStatus.SUSPENDED:
            await self._resume()

    async def save_state(self) -> None:
        """
        Save executor state and coordinate NodeActor state saves
        Only works for root executor - collects and saves entire tree state
        """
        if self.is_child:
            return

        snapshot = {}
        stack: list[Executor] = [self]

        while stack:
            executor = stack.pop()

            executor_key = str(executor.execution_id)
            snapshot[executor_key] = executor.state.model_dump()

            # Save executor's NodeActor state
            if executor.node_actor:
                actor_state = executor.node_actor.serialize_state()
                await self.state_storage.asave_actor_state(
                    self.execution_id, executor.node_actor.id, actor_state
                )

            for child_executor in executor.child_executors.values():
                stack.append(child_executor)

        await self.state_storage.asave_executor_state(self.execution_id, snapshot)

    async def _get_or_create_node_actor(
        self, input_: ExecutorInput, node: BaseNode[S, NS]
    ) -> NodeActor[S, NS]:
        try:
            _, node_actor = self._find_target_for_input(input_)
        except ValueError:
            node_actor = NodeActor.create(node, llm=self.llm)
            actor_state = self.node_actor.serialize_state()
            await self.state_storage.asave_actor_state(
                input_.execution_id, node_actor.id, actor_state
            )
        return node_actor

    def _find_target_for_input(
        self, input_: ExecutorInput
    ) -> tuple[Executor, NodeActor[Any, Any]]:
        """
        Find the target executor and node actor for the given input

        Returns:
            Tuple of (target_executor, target_node_actor)
        """
        # Check if this executor has the target node actor
        if self.node_actor and self.node_actor.id == input_.node_actor_id:
            return self, self.node_actor

        # Check child executors for the target node actor
        child_executor = self.child_executors.get(input_.execution_id)
        if not child_executor:
            raise ValueError(
                f"Executor with execution id {input_.execution_id} not found"
            )

        if (
            child_executor.node_actor
            and child_executor.node_actor.id == input_.node_actor_id
        ):
            return child_executor, child_executor.node_actor

        raise ValueError(
            f"Target executor and node actor with ID {input_.node_actor_id} not found"
        )

    async def _bubble_up_completion(self, result: Result[S, NS]) -> None:
        """
        Bubble up completion to parent executor if exists
        """
        self.state.status = ExecutorStatus.COMPLETED
        await self.root_executor.save_state()
        if self.parent_executor:
            await self.parent_executor.handle_child_completed(self.execution_id)

    async def _execute_parallel(
        self, next_nodes: list[tuple[BaseNode[S, NS], Any]]
    ) -> list[ExecutorOutput]:
        """
        Execute paralle nodes
        """
        # Fork executors for each branch
        branches = await self._fork(next_nodes)
        # Save state after forking
        self.state.status = ExecutorStatus.SUSPENDED
        await self.root_executor.save_state()

        async def execute_child(executor: Executor, input_: Any) -> ExecutorOutput:
            return await executor.step(input_)

        tasks = [execute_child(executor, input_) for executor, input_ in branches]
        outputs = await asyncio.gather(*tasks, return_exceptions=True)

        # Save state after forking
        self.state.status = ExecutorStatus.RUNNING
        await self.root_executor.save_state()
        # Filter out exceptions and None results
        valid_outputs = [
            output for output in outputs if isinstance(output, ExecutorOutput)
        ]
        return valid_outputs

    async def _fork(
        self, nodes: list[tuple[BaseNode[S, NS], Any]]
    ) -> list[tuple[Executor, ExecutorInput]]:
        """
        Fork executor for parallel branch execution
        """
        child_executors: list[tuple[Executor, ExecutorInput]] = []
        for node, node_input in nodes:
            node_actor = NodeActor.create(node, llm=self.llm)
            await node_actor.ainitialize()

            child_executor = Executor(
                registry=self.registry,
                state_storage=self.state_storage,
                llm=self.llm,
                node_actor=node_actor,
                parent_executor=self,
            )

            # Add to children
            self.state.child_executor_ids.add(child_executor.execution_id)
            self.child_executors[child_executor.execution_id] = child_executor
            input_ = ExecutorInput(
                execution_id=child_executor.execution_id,
                node_actor_id=node_actor.id,
                node_input=node_input,
            )
            child_executors.append((child_executor, input_))

        return child_executors

    async def _resume(self) -> BaseMessage:
        """
        Resume execution after children complete, merging their results
        """

        # Collect results from completed children
        results = []
        for child in self.child_executors.values():
            if child.state.status == ExecutorStatus.COMPLETED:
                # Get the final response from child's node actor if available
                if child.node_actor and hasattr(child.node_actor, "last_response"):
                    results.append(str(child.node_actor.last_response.content))
                else:
                    results.append("")

        # Merge results
        combined_content = "\n\n".join(results)
        merged_result = HumanMessage(content=combined_content)

        # Resume this executor
        self.state.status = ExecutorStatus.RUNNING

        self.child_executors.clear()
        self.state.child_executor_ids.clear()

        return merged_result
