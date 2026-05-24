from uuid import uuid4

import pytest

from liman.state import InMemoryStateStorage


def test_in_memory_storage_init() -> None:
    storage = InMemoryStateStorage()
    assert storage.executor_states == {}
    assert storage.actor_states == {}


@pytest.mark.asyncio
async def test_save_and_load_executor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    state = {"key": "value", "count": 42}

    await storage.save_executor_state(execution_id, state)
    loaded_state = await storage.load_executor_state(execution_id)

    assert loaded_state == state


@pytest.mark.asyncio
async def test_load_nonexistent_executor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()

    loaded_state = await storage.load_executor_state(execution_id)

    assert loaded_state is None


@pytest.mark.asyncio
async def test_save_and_load_actor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    actor_id = uuid4()
    state = {"actor_key": "actor_value", "status": "running"}

    await storage.save_actor_state(execution_id, actor_id, state)
    loaded_state = await storage.load_actor_state(execution_id, actor_id)

    assert loaded_state == state


@pytest.mark.asyncio
async def test_load_nonexistent_actor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    actor_id = uuid4()

    loaded_state = await storage.load_actor_state(execution_id, actor_id)

    assert loaded_state is None


@pytest.mark.asyncio
async def test_load_actor_state_nonexistent_execution() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    actor_id = uuid4()

    loaded_state = await storage.load_actor_state(execution_id, actor_id)

    assert loaded_state is None


@pytest.mark.asyncio
async def test_multiple_actors_same_execution() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    actor_id_1 = uuid4()
    actor_id_2 = uuid4()
    state_1 = {"actor": "first"}
    state_2 = {"actor": "second"}

    await storage.save_actor_state(execution_id, actor_id_1, state_1)
    await storage.save_actor_state(execution_id, actor_id_2, state_2)

    loaded_state_1 = await storage.load_actor_state(execution_id, actor_id_1)
    loaded_state_2 = await storage.load_actor_state(execution_id, actor_id_2)

    assert loaded_state_1 == state_1
    assert loaded_state_2 == state_2


@pytest.mark.asyncio
async def test_delete_executor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    actor_id = uuid4()
    executor_state = {"executor": "state"}
    actor_state = {"actor": "state"}

    await storage.save_executor_state(execution_id, executor_state)
    await storage.save_actor_state(execution_id, actor_id, actor_state)

    await storage.delete_executor_state(execution_id)

    assert await storage.load_executor_state(execution_id) is None
    assert await storage.load_actor_state(execution_id, actor_id) is None


@pytest.mark.asyncio
async def test_delete_nonexistent_executor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()

    await storage.delete_executor_state(execution_id)


@pytest.mark.asyncio
async def test_overwrite_executor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    state_1 = {"version": 1}
    state_2 = {"version": 2}

    await storage.save_executor_state(execution_id, state_1)
    await storage.save_executor_state(execution_id, state_2)

    loaded_state = await storage.load_executor_state(execution_id)
    assert loaded_state == state_2


@pytest.mark.asyncio
async def test_overwrite_actor_state() -> None:
    storage = InMemoryStateStorage()
    execution_id = uuid4()
    actor_id = uuid4()
    state_1 = {"version": 1}
    state_2 = {"version": 2}

    await storage.save_actor_state(execution_id, actor_id, state_1)
    await storage.save_actor_state(execution_id, actor_id, state_2)

    loaded_state = await storage.load_actor_state(execution_id, actor_id)
    assert loaded_state == state_2
