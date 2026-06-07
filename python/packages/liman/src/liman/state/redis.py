import json
from typing import Any
from uuid import UUID

try:
    import redis.asyncio as redis
except ImportError as e:
    raise ImportError("Install liman[redis] to use RedisStateStorage") from e

from liman.state.base import StateStorage


class RedisStateStorage(StateStorage):
    """
    Redis-backed state storage.

    Keys are namespaced by user_id when provided in context:
      liman:{user_id}:{executor_id}:executor
      liman:{user_id}:{executor_id}:{actor_id}:actor

    Without user_id:
      liman:{executor_id}:executor
      liman:{executor_id}:{actor_id}:actor
    """

    def __init__(self, client: redis.Redis) -> None:
        self.client = client

    async def save_executor_state(
        self,
        executor_id: UUID,
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> None:
        key = self._executor_key(executor_id, context)
        await self.client.set(key, json.dumps(state))

    async def load_executor_state(
        self, executor_id: UUID, *, context: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        key = self._executor_key(executor_id, context)
        raw = await self.client.get(key)
        if raw is None:
            return None
        state = json.loads(raw)
        if not isinstance(state, dict):
            return None
        return state

    async def delete_executor_state(
        self, executor_id: UUID, *, context: dict[str, Any] | None = None
    ) -> None:
        executor_key = self._executor_key(executor_id, context)
        user_id = (context or {}).get("user_id")
        if user_id:
            pattern = f"liman:{user_id}:{executor_id}:*"
        else:
            pattern = f"liman:{executor_id}:*"
        keys = await self.client.keys(pattern)
        if keys:
            await self.client.delete(*keys)
        else:
            await self.client.delete(executor_key)

    async def save_actor_state(
        self,
        executor_id: UUID,
        actor_id: UUID,
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> None:
        key = self._actor_key(executor_id, actor_id, context)
        await self.client.set(key, json.dumps(state))

    async def load_actor_state(
        self,
        executor_id: UUID,
        actor_id: UUID,
        *,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        key = self._actor_key(executor_id, actor_id, context)
        raw = await self.client.get(key)
        if raw is None:
            return None
        state = json.loads(raw)
        if not isinstance(state, dict):
            return None
        return state

    def _executor_key(self, executor_id: UUID, context: dict[str, Any] | None) -> str:
        user_id = (context or {}).get("user_id")
        if user_id:
            return f"liman:{user_id}:{executor_id}:executor"
        return f"liman:{executor_id}:executor"

    def _actor_key(
        self, executor_id: UUID, actor_id: UUID, context: dict[str, Any] | None
    ) -> str:
        user_id = (context or {}).get("user_id")
        if user_id:
            return f"liman:{user_id}:{executor_id}:{actor_id}:actor"
        return f"liman:{executor_id}:{actor_id}:actor"
