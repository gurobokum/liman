from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class StateStorage(ABC):
    """
    Abstract interface for state persistence.

    There are two types of state:
    1. Executor state: Tracks the overall execution flow of the executor.
    2. NodeActor state: Tracks the internal state of each individual node actor.

    The context parameter provides extra information,
    such as a user ID for saving user-specific state or other metadata useful for the storage backend.
    """

    @abstractmethod
    async def save_executor_state(
        self,
        executor_id: UUID,
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> None: ...

    @abstractmethod
    async def load_executor_state(
        self, executor_id: UUID, *, context: dict[str, Any] | None = None
    ) -> dict[str, Any] | None: ...

    @abstractmethod
    async def delete_executor_state(
        self, executor_id: UUID, *, context: dict[str, Any] | None = None
    ) -> None: ...

    @abstractmethod
    async def save_actor_state(
        self,
        executor_id: UUID,
        actor_id: UUID,
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> None: ...

    @abstractmethod
    async def load_actor_state(
        self,
        executor_id: UUID,
        actor_id: UUID,
        *,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None: ...


class InMemoryStateStorage(StateStorage):
    """
    In-memory state storage for testing
    """

    def __init__(self) -> None:
        self.executor_states: dict[UUID, dict[str, Any]] = {}
        self.actor_states: dict[UUID, dict[UUID, dict[str, Any]]] = {}

    async def save_executor_state(
        self,
        executor_id: UUID,
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.executor_states[executor_id] = state

    async def load_executor_state(
        self, executor_id: UUID, *, context: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        return self.executor_states.get(executor_id)

    async def delete_executor_state(
        self, executor_id: UUID, *, context: dict[str, Any] | None = None
    ) -> None:
        self.executor_states.pop(executor_id, None)
        self.actor_states.pop(executor_id, None)

    async def save_actor_state(
        self,
        executor_id: UUID,
        actor_id: UUID,
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> None:
        if executor_id not in self.actor_states:
            self.actor_states[executor_id] = {}
        self.actor_states[executor_id][actor_id] = state

    async def load_actor_state(
        self,
        executor_id: UUID,
        actor_id: UUID,
        *,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        return self.actor_states.get(executor_id, {}).get(actor_id)
