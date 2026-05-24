import asyncio
import logging
from asyncio import Queue, Task
from typing import Any
from uuid import UUID, uuid4

from langchain_core.language_models.chat_models import BaseChatModel
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
        self._root_executor: Executor | None = None
        self._executors: dict[UUID, Executor] = {}

        load_specs_from_directory(self.specs_dir, self.registry)

    async def step(
        self, input_: str | ExecutorInput, context: dict[str, Any] | None = None
    ) -> ExecutorOutput:
        self.logger.debug("Agent '%s' received input: %s", self.name, repr(input_))

        if isinstance(input_, ExecutorInput):
            if context:
                intersection = set(input_.context or {}) & set(context)
                if intersection:
                    self.logger.warning("Overwriting keys in context: %s", intersection)
                input_.context = (
                    {**input_.context, **context} if input_.context else context
                )
            await self._input_queue.put(input_)
        else:
            input_ = await self._create_executor_input(input_, context)
            await self._input_queue.put(input_)

        if not self._processing_task:
            self._processing_task = asyncio.create_task(self._process_input_loop())
            self._processing_task.add_done_callback(self._on_exit_input_loop)

        res = await self._output_queue.get()
        return res

    async def _process_input_loop(self) -> None:
        while True:
            if self.iteration_count >= self.max_iterations:
                raise RuntimeError(
                    f"Agent exceeded max iterations ({self.max_iterations})"
                )

            input_ = await self._input_queue.get()
            self.iteration_count += 1

            executor = await self._get_or_create_executor(input_)

            output = await executor.step(input_)

            await self._output_queue.put(output)
            if output.exit_:
                self.logger.debug("Agent '%s' completed execution", self.name)
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

    async def _get_or_create_executor(self, input_: str | ExecutorInput) -> Executor:
        executor: Executor | None = None

        if isinstance(input_, str):
            if not self._root_executor:
                executor = Executor(
                    registry=self.registry,
                    state_storage=self.state_storage,
                    llm=self.llm,
                    max_iterations=self.max_iterations,
                )
                self.logger.debug(
                    "Clean root executor created for agent %s with executor_id: %s",
                    self.name,
                    executor.id,
                )
                self._executors[executor.execution_id] = self._root_executor = executor
            return self._root_executor

        executor = self._executors.get(input_.execution_id)
        if executor:
            return executor

        executor = await Executor.restore_or_create(
            registry=self.registry,
            state_storage=self.state_storage,
            llm=self.llm,
            execution_id=input_.execution_id,
            max_iterations=self.max_iterations,
        )

        self._executors[executor.execution_id] = executor
        return executor

    async def _create_executor_input(
        self, input_: str, context: dict[str, Any] | None = None
    ) -> ExecutorInput:
        """
        If the input is a plain string, send it to the root executor.
        """
        executor = self._root_executor
        if not executor:
            executor = await self._get_or_create_executor(input_)

        return ExecutorInput(
            executor_id=executor.id,
            execution_id=executor.execution_id,
            node_input=input_,
            node_fullname=self.start_node,
            context=context,
        )
