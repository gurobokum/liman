from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


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

    @abstractmethod
    async def save_executor_state(
        self, execution_id: UUID, state: dict[str, Any]
    ) -> None: ...

    @abstractmethod
    async def load_executor_state(
        self, execution_id: UUID
    ) -> dict[str, Any] | None: ...

    @abstractmethod
    async def save_actor_state(
        self, execution_id: UUID, actor_id: UUID, state: dict[str, Any]
    ) -> None: ...

    @abstractmethod
    async def load_actor_state(
        self, execution_id: UUID, actor_id: UUID
    ) -> dict[str, Any] | None: ...

    @abstractmethod
    async def delete_execution_state(self, execution_id: UUID) -> None: ...


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

    async def save_actor_state(
        self, execution_id: UUID, actor_id: UUID, state: dict[str, Any]
    ) -> None:
        if execution_id not in self.actor_states:
            self.actor_states[execution_id] = {}
        self.actor_states[execution_id][actor_id] = state

    async def load_actor_state(
        self, execution_id: UUID, actor_id: UUID
    ) -> dict[str, Any] | None:
        return self.actor_states.get(execution_id, {}).get(actor_id)

    async def delete_execution_state(self, execution_id: UUID) -> None:
        self.executor_states.pop(execution_id, None)
        self.actor_states.pop(execution_id, None)

    # Async methods - delegate to sync methods
    async def asave_executor_state(
        self, execution_id: UUID, state: dict[str, Any]
    ) -> None:
        await self.save_executor_state(execution_id, state)

    async def aload_executor_state(self, execution_id: UUID) -> dict[str, Any] | None:
        return await self.load_executor_state(execution_id)

    async def asave_actor_state(
        self, execution_id: UUID, actor_id: UUID, state: dict[str, Any]
    ) -> None:
        await self.save_actor_state(execution_id, actor_id, state)

    async def aload_actor_state(
        self, execution_id: UUID, actor_id: UUID
    ) -> dict[str, Any] | None:
        return await self.load_actor_state(execution_id, actor_id)

    async def adelete_execution_state(self, execution_id: UUID) -> None:
        await self.delete_execution_state(execution_id)
