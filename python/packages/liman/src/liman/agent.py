import asyncio
import logging
from asyncio import Queue, Task
from typing import Any, TypedDict
from uuid import UUID, uuid4

from langchain_core.language_models.chat_models import BaseChatModel
from liman_core.errors import LimanError
from liman_core.node_actor.actor import NodeActor
from liman_core.nodes.llm_node.node import LLMNode
from liman_core.nodes.supported_types import get_node_cls
from liman_core.registry import Registry

from liman.conf import settings
from liman.executor.base import Executor
from liman.executor.schemas import ExecutorInput, ExecutorOutput
from liman.loader import load_specs_from_directory
from liman.state import InMemoryStateStorage, StateStorage

logger = logging.getLogger(__name__)

if settings.DEBUG:
    try:
        from rich.logging import RichHandler
    except ImportError:
        logger.warning(
            "Rich logging is not available. Install 'rich' package to enable rich logging."
        )
    else:
        handler = RichHandler(show_time=True, show_path=True, rich_tracebacks=True)
        handler.setFormatter(
            logging.Formatter("%(agent_id)s [%(agent_name)s] %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)


class NodeAgentConfig(TypedDict):
    """
    NodeActor configuration that allows the agent to direct input there.
    """

    node_actor_id: UUID
    execution_id: UUID
    node_full_name: str


class Agent:
    def __init__(
        self,
        specs_dir: str,
        start_node: str,
        *,
        name: str = "Agent",
        llm: BaseChatModel,
        registry: Registry | None = None,
        state_storage: StateStorage | None = None,
        max_iterations: int = 50,
    ):
        self.id = uuid4()
        self.specs_dir = specs_dir
        self.name = name
        self.llm = llm
        self.start_node = start_node

        self.registry = registry or Registry()
        self.state_storage = state_storage or InMemoryStateStorage()

        self.iteration_count = 0
        self.max_iterations = max_iterations

        self._input_queue: Queue[ExecutorInput] = Queue()
        self._output_queue: Queue[ExecutorOutput] = Queue()

        self.logger = logging.LoggerAdapter(
            logger, {"agent_id": str(self.id), "agent_name": self.name}
        )

        self._processing_task: Task[None] | None = None
        self._executor: Executor | None = None
        self._last_node_actor_cfg: NodeAgentConfig | None = None

        load_specs_from_directory(self.specs_dir, self.registry)

    async def step(
        self, input_: str | ExecutorInput, context: dict[str, Any] | None = None
    ) -> ExecutorOutput:
        self.logger.debug(f"Agent '{self.name}' received input: {repr(input_)}")

        if not self._executor:
            self._executor = await self._create_executor(input_)
            self.logger.debug(
                f"Root executor created for agent '{self.name}' with execution ID: {self._executor.execution_id}"
            )

        if isinstance(input_, ExecutorInput):
            if context:
                intersection = set(input_.context or {}) & set(context)
                if intersection:
                    self.logger.warning(f"Overwriting keys in context: {intersection}")
                input_.context = (
                    {**input_.context, **context} if input_.context else context
                )
            await self._input_queue.put(input_)
        else:
            input_ = self._create_executor_input(input_, context)
            await self._input_queue.put(input_)

        if not self._processing_task:
            self._processing_task = asyncio.create_task(self._process_input_loop())
            self._processing_task.add_done_callback(self._on_exit_input_loop)

        res = await self._output_queue.get()
        return res

    async def _process_input_loop(self) -> None:
        async def deferred_put(output: ExecutorOutput) -> None:
            """
            Deferred put to the output queue to ensure that the task is not blocked
            by any sync call outside, like input()
            """
            await self._output_queue.put(output)

        while True:
            if self.iteration_count >= self.max_iterations:
                raise RuntimeError(
                    f"Agent exceeded max iterations ({self.max_iterations})"
                )

            input_ = await self._input_queue.get()
            self.iteration_count += 1

            if not self._executor:
                raise LimanError("Executor is not created. [CRITICAL]")

            output = await self._executor.step(input_)
            self._last_node_actor_cfg = self._get_node_actor_cfg(output)

            asyncio.create_task(deferred_put(output))
            if output.exit_:
                self.logger.debug(f"Agent '{self.name}' completed execution")
                return

    def _on_exit_input_loop(self, task: Task[None]) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            ...
        except Exception:
            raise
        finally:
            self.logger.debug("Agent stopped processing input loop")
            self._processing_task = None

    def _get_node_actor_cfg(self, output: ExecutorOutput) -> NodeAgentConfig:
        return {
            "node_actor_id": output.node_actor_id,
            "execution_id": output.execution_id,
            "node_full_name": output.node_full_name,
        }

    async def _create_initial_node_actor(
        self, input_: ExecutorInput, execution_id: UUID
    ) -> NodeActor[Any]:
        node_cls, node_name = input_.node_full_name.split("/")
        node = self.registry.lookup(get_node_cls(node_cls), node_name)

        node_actor = await NodeActor.create_or_restore(node, llm=self.llm, state=None)
        actor_state = node_actor.serialize_state()
        await self.state_storage.asave_actor_state(
            execution_id, node_actor.id, actor_state
        )
        return node_actor

    async def _create_executor(self, input_: str | ExecutorInput) -> Executor:
        if isinstance(input_, ExecutorInput):
            execution_id = input_.execution_id
        else:
            if len(self.start_node.split("/")) == 2:
                node_cls, node_name = self.start_node.split("/")
                node = self.registry.lookup(get_node_cls(node_cls), node_name)
            else:
                # If start_node is just a node name, lookup by LLMNode
                node = self.registry.lookup(LLMNode, self.start_node)

            execution_id = uuid4()
            node_actor_id = uuid4()
            input_ = ExecutorInput(
                execution_id=execution_id,
                node_actor_id=node_actor_id,
                node_input=input_,
                node_full_name=node.full_name,
            )

        node_actor = await self._create_initial_node_actor(input_, execution_id)
        return Executor(
            registry=self.registry,
            state_storage=self.state_storage,
            node_actor=node_actor,
            llm=self.llm,
            execution_id=execution_id,
            max_iterations=self.max_iterations,
        )

    def _create_executor_input(
        self, input_: str, context: dict[str, Any] | None = None
    ) -> ExecutorInput:
        if cfg := self._last_node_actor_cfg:
            return ExecutorInput(
                execution_id=cfg["execution_id"],
                node_actor_id=cfg["node_actor_id"],
                node_input=input_,
                node_full_name=cfg["node_full_name"],
                context=context,
            )
        else:
            if not self._executor:
                raise RuntimeError("Executor is not created yet.")
            return ExecutorInput(
                execution_id=self._executor.execution_id,
                node_actor_id=self._executor.node_actor.id,
                node_input=input_,
                node_full_name=self._executor.node_actor.node.full_name,
                context=context,
            )
