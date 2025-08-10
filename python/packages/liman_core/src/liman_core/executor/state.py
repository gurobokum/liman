from abc import ABC, abstractmethod
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ExecutorStatus(str, Enum):
    """
    Status of an executor in the tree
    """

    RUNNING = "running"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutorState(BaseModel):
    """
    Executor state that can restore the execution tree structure.

    Root Executor (01a1dd9a-9374-44e7-b8a8-7fc891b29de0) - SUSPENDED
      ├── Child Executor 1 (child1) - SUSPENDED
      ├── Child Executor 2 (cda81fa7-75f1-4800-bc2b-3aae70aa0e60) - SUSPENDED
      │     ├── Sub Executor 3 (f1e2d3c4-5678-90ab-cdef-1234567890ab) - COMPLETED
      │     └── Sub Executor 4 (a1b2c3d4-5678-90ab-cdef-1234567890ab) - RUNNING
      └── Child Executor 3 (b1c2d3e4-5678-90ab-cdef-1234567890ab) - RUNNING

    """

    execution_id: UUID
    node_actor_id: UUID

    status: ExecutorStatus

    child_executor_ids: set[UUID] = set()
    iteration_count: int = 0
    is_child: bool = False


class StateStorage(ABC):
    """
    Abstract interface for state persistence - supports both sync and async operations
    """

    # Async methods
    @abstractmethod
    async def asave_executor_state(
        self, execution_id: UUID, state: dict[str, Any]
    ) -> None: ...

    @abstractmethod
    async def aload_executor_state(
        self, execution_id: UUID
    ) -> dict[str, Any] | None: ...

    @abstractmethod
    async def asave_actor_state(
        self, execution_id: UUID, actor_id: UUID, state: dict[str, Any]
    ) -> None: ...

    @abstractmethod
    async def aload_actor_state(
        self, execution_id: UUID, actor_id: UUID
    ) -> dict[str, Any] | None: ...

    @abstractmethod
    async def adelete_execution_state(self, execution_id: UUID) -> None: ...

    # Sync methods
    @abstractmethod
    def save_executor_state(
        self, execution_id: UUID, state: dict[str, Any]
    ) -> None: ...

    @abstractmethod
    def load_executor_state(self, execution_id: UUID) -> dict[str, Any] | None: ...

    @abstractmethod
    def save_actor_state(
        self, execution_id: UUID, actor_id: UUID, state: dict[str, Any]
    ) -> None: ...

    @abstractmethod
    def load_actor_state(
        self, execution_id: UUID, actor_id: UUID
    ) -> dict[str, Any] | None: ...

    @abstractmethod
    def delete_execution_state(self, execution_id: UUID) -> None: ...


class InMemoryStateStorage(StateStorage):
    """
    In-memory state storage for testing
    """

    def __init__(self) -> None:
        self.executor_states: dict[UUID, dict[str, Any]] = {}
        self.actor_states: dict[UUID, dict[UUID, dict[str, Any]]] = {}

    # Sync methods
    def save_executor_state(self, execution_id: UUID, state: dict[str, Any]) -> None:
        self.executor_states[execution_id] = state

    def load_executor_state(self, execution_id: UUID) -> dict[str, Any] | None:
        return self.executor_states.get(execution_id)

    def save_actor_state(
        self, execution_id: UUID, actor_id: UUID, state: dict[str, Any]
    ) -> None:
        if execution_id not in self.actor_states:
            self.actor_states[execution_id] = {}
        self.actor_states[execution_id][actor_id] = state

    def load_actor_state(
        self, execution_id: UUID, actor_id: UUID
    ) -> dict[str, Any] | None:
        return self.actor_states.get(execution_id, {}).get(actor_id)

    def delete_execution_state(self, execution_id: UUID) -> None:
        self.executor_states.pop(execution_id, None)
        self.actor_states.pop(execution_id, None)

    # Async methods - delegate to sync methods
    async def asave_executor_state(
        self, execution_id: UUID, state: dict[str, Any]
    ) -> None:
        self.save_executor_state(execution_id, state)

    async def aload_executor_state(self, execution_id: UUID) -> dict[str, Any] | None:
        return self.load_executor_state(execution_id)

    async def asave_actor_state(
        self, execution_id: UUID, actor_id: UUID, state: dict[str, Any]
    ) -> None:
        self.save_actor_state(execution_id, actor_id, state)

    async def aload_actor_state(
        self, execution_id: UUID, actor_id: UUID
    ) -> dict[str, Any] | None:
        return self.load_actor_state(execution_id, actor_id)

    async def adelete_execution_state(self, execution_id: UUID) -> None:
        self.delete_execution_state(execution_id)
