from uuid import uuid4

import pytest

from liman.state import InMemoryStateStorage


def test_in_memory_storage_init() -> None:
    storage = InMemoryStateStorage()
    assert storage.executor_states == {}
    assert storage.actor_states == {}


def test_save_and_load_executor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    state = {"key": "value", "count": 42}

    storage.save_executor_state(execution_id, state)
    loaded_state = storage.load_executor_state(execution_id)

    assert loaded_state == state


def test_load_nonexistent_executor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()

    loaded_state = storage.load_executor_state(execution_id)

    assert loaded_state is None


def test_save_and_load_actor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    actor_id = uuid4()
    state = {"actor_key": "actor_value", "status": "running"}

    storage.save_actor_state(execution_id, actor_id, state)
    loaded_state = storage.load_actor_state(execution_id, actor_id)

    assert loaded_state == state


def test_load_nonexistent_actor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    actor_id = uuid4()

    loaded_state = storage.load_actor_state(execution_id, actor_id)

    assert loaded_state is None


def test_load_actor_state_nonexistent_execution() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    actor_id = uuid4()

    loaded_state = storage.load_actor_state(execution_id, actor_id)

    assert loaded_state is None


def test_multiple_actors_same_execution() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    actor_id_1 = uuid4()
    actor_id_2 = uuid4()
    state_1 = {"actor": "first"}
    state_2 = {"actor": "second"}

    storage.save_actor_state(execution_id, actor_id_1, state_1)
    storage.save_actor_state(execution_id, actor_id_2, state_2)

    loaded_state_1 = storage.load_actor_state(execution_id, actor_id_1)
    loaded_state_2 = storage.load_actor_state(execution_id, actor_id_2)

    assert loaded_state_1 == state_1
    assert loaded_state_2 == state_2


def test_delete_execution_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    actor_id = uuid4()
    executor_state = {"executor": "state"}
    actor_state = {"actor": "state"}

    storage.save_executor_state(execution_id, executor_state)
    storage.save_actor_state(execution_id, actor_id, actor_state)

    storage.delete_execution_state(execution_id)

    assert storage.load_executor_state(execution_id) is None
    assert storage.load_actor_state(execution_id, actor_id) is None


def test_delete_nonexistent_execution_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()

    storage.delete_execution_state(execution_id)


def test_overwrite_executor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    state_1 = {"version": 1}
    state_2 = {"version": 2}

    storage.save_executor_state(execution_id, state_1)
    storage.save_executor_state(execution_id, state_2)

    loaded_state = storage.load_executor_state(execution_id)
    assert loaded_state == state_2


def test_overwrite_actor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    actor_id = uuid4()
    state_1 = {"version": 1}
    state_2 = {"version": 2}

    storage.save_actor_state(execution_id, actor_id, state_1)
    storage.save_actor_state(execution_id, actor_id, state_2)

    loaded_state = storage.load_actor_state(execution_id, actor_id)
    assert loaded_state == state_2


@pytest.mark.asyncio
async def test_asave_and_aload_executor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    state = {"async_key": "async_value", "count": 42}

    await storage.asave_executor_state(execution_id, state)
    loaded_state = await storage.aload_executor_state(execution_id)

    assert loaded_state == state


@pytest.mark.asyncio
async def test_aload_nonexistent_executor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()

    loaded_state = await storage.aload_executor_state(execution_id)

    assert loaded_state is None


@pytest.mark.asyncio
async def test_asave_and_aload_actor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    actor_id = uuid4()
    state = {"async_actor_key": "async_actor_value", "status": "running"}

    await storage.asave_actor_state(execution_id, actor_id, state)
    loaded_state = await storage.aload_actor_state(execution_id, actor_id)

    assert loaded_state == state


@pytest.mark.asyncio
async def test_aload_nonexistent_actor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    actor_id = uuid4()

    loaded_state = await storage.aload_actor_state(execution_id, actor_id)

    assert loaded_state is None


@pytest.mark.asyncio
async def test_adelete_execution_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    actor_id = uuid4()
    executor_state = {"async_executor": "state"}
    actor_state = {"async_actor": "state"}

    await storage.asave_executor_state(execution_id, executor_state)
    await storage.asave_actor_state(execution_id, actor_id, actor_state)

    await storage.adelete_execution_state(execution_id)

    assert await storage.aload_executor_state(execution_id) is None
    assert await storage.aload_actor_state(execution_id, actor_id) is None


@pytest.mark.asyncio
async def test_async_sync_consistency() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    actor_id = uuid4()
    executor_state = {"executor": "sync_saved"}
    actor_state = {"actor": "async_saved"}

    storage.save_executor_state(execution_id, executor_state)
    await storage.asave_actor_state(execution_id, actor_id, actor_state)

    async_executor_state = await storage.aload_executor_state(execution_id)
    sync_actor_state = storage.load_actor_state(execution_id, actor_id)

    assert async_executor_state == executor_state
    assert sync_actor_state == actor_state
