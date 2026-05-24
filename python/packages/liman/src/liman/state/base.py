from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class StateStorage(ABC):
    """
    Abstract interface for state persistence
    """

    @abstractmethod
    async def save_executor_state(
        self, executor_id: UUID, state: dict[str, Any]
    ) -> None: ...

    @abstractmethod
    async def load_executor_state(self, executor_id: UUID) -> dict[str, Any] | None: ...

    @abstractmethod
    async def delete_executor_state(self, executor_id: UUID) -> None: ...

    @abstractmethod
    async def save_actor_state(
        self, executor_id: UUID, actor_id: UUID, state: dict[str, Any]
    ) -> None: ...

    @abstractmethod
    async def load_actor_state(
        self, executor_id: UUID, actor_id: UUID
    ) -> dict[str, Any] | None: ...


class InMemoryStateStorage(StateStorage):
    """
    In-memory state storage for testing
    """

    def __init__(self) -> None:
        self.executor_states: dict[UUID, dict[str, Any]] = {}
        self.actor_states: dict[UUID, dict[UUID, dict[str, Any]]] = {}

    async def save_executor_state(
        self, executor_id: UUID, state: dict[str, Any]
    ) -> None:
        self.executor_states[executor_id] = state

    async def load_executor_state(self, executor_id: UUID) -> dict[str, Any] | None:
        return self.executor_states.get(executor_id)

    async def delete_executor_state(self, executor_id: UUID) -> None:
        self.executor_states.pop(executor_id, None)
        self.actor_states.pop(executor_id, None)

    async def save_actor_state(
        self, executor_id: UUID, actor_id: UUID, state: dict[str, Any]
    ) -> None:
        if executor_id not in self.actor_states:
            self.actor_states[executor_id] = {}
        self.actor_states[executor_id][actor_id] = state

    async def load_actor_state(
        self, executor_id: UUID, actor_id: UUID
    ) -> dict[str, Any] | None:
        return self.actor_states.get(executor_id, {}).get(actor_id)
