import asyncio
from typing import Any

import pytest
from langchain_core.messages import ToolMessage

from liman_core.dishka import FromLiman, Scope
from liman_core.nodes.base.execution_context import ExecutionContext
from liman_core.nodes.tool_node.node import ToolNode
from liman_core.nodes.tool_node.schemas import ToolCall, ToolNodeState
from liman_core.registry import Registry


class Database:
    def __init__(self, name: str, connection_string: str) -> None:
        self.name = name
        self.connection_string = connection_string

    def query(self, sql: str) -> str:
        return f"DB[{self.name}] executed: {sql}"


class UserService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_user(self, user_id: str) -> str:
        return f"User({user_id}) from {self.db.name}"


class UnprovidedDatabase:
    def __init__(self, name: str) -> None:
        self.name = name

    def query(self, sql: str) -> str:
        return f"DB[{self.name}] executed: {sql}"


def get_database() -> Database:
    return Database(name="test_db", connection_string="sqlite://test")


def get_user_service(db: Database) -> UserService:
    return UserService(db)


def tool_with_from_liman_db(message: str, db: FromLiman[Database]) -> str:
    result = db.query(f"INSERT INTO messages VALUES ('{message}')")
    return f"Message stored: {result}"


def tool_with_multiple_dependencies(
    action: str, db: FromLiman[Database], user_service: FromLiman[UserService]
) -> str:
    user = user_service.get_user("123")
    query_result = db.query(f"SELECT * FROM {action}")
    return f"{user} performed action: {query_result}"


def tool_mixed_params(message: str, count: int, db: FromLiman[Database]) -> str:
    for i in range(count):
        db.query(f"INSERT INTO logs VALUES ('{message}_{i}')")
    return f"Inserted {count} records into {db.name}"


def tool_with_unprovided_dependency(
    message: str, db: FromLiman[UnprovidedDatabase]
) -> str:
    result = db.query(f"INSERT INTO messages VALUES ('{message}')")
    return f"Message stored: {result}"


@pytest.fixture
def from_liman_tool_decl() -> dict[str, Any]:
    return {
        "kind": "ToolNode",
        "name": "from_liman_tool",
        "description": {"en": "Tool with FromLiman dependency"},
        "arguments": [
            {
                "name": "message",
                "type": "str",
                "description": {"en": "Message to store"},
            }
        ],
    }


@pytest.fixture
def multi_dep_tool_decl() -> dict[str, Any]:
    return {
        "kind": "ToolNode",
        "name": "multi_dep_tool",
        "description": {"en": "Tool with multiple dependencies"},
        "arguments": [
            {
                "name": "action",
                "type": "str",
                "description": {"en": "Action to perform"},
            }
        ],
    }


@pytest.fixture
def mixed_tool_decl() -> dict[str, Any]:
    return {
        "kind": "ToolNode",
        "name": "mixed_tool",
        "description": {"en": "Tool with mixed parameters"},
        "arguments": [
            {
                "name": "message",
                "type": "str",
                "description": {"en": "Message to log"},
            },
            {
                "name": "count",
                "type": "int",
                "description": {"en": "Number of records"},
            },
        ],
    }


def _make_execution_context(node: ToolNode) -> ExecutionContext[ToolNodeState]:
    return ExecutionContext(ToolNodeState(kind=node.spec.kind, name=node.spec.name))


def test_from_liman_database_injection(
    from_liman_tool_decl: dict[str, Any], registry: Registry
) -> None:
    registry.provide(get_database, scope=Scope.NODE)

    node = ToolNode.from_dict(from_liman_tool_decl, registry)
    node.set_func(tool_with_from_liman_db)

    tool_call = ToolCall.model_validate(
        {
            "name": "from_liman_tool",
            "args": {"message": "hello world"},
            "id": "call_123",
            "type": "tool_call",
        }
    )

    result = asyncio.run(node.invoke(tool_call, _make_execution_context(node)))

    assert isinstance(result, ToolMessage)
    assert (
        "Message stored: DB[test_db] executed: INSERT INTO messages VALUES "
        "('hello world')"
    ) in result.content
    assert result.tool_call_id == "call_123"


def test_multiple_from_liman_dependencies(
    multi_dep_tool_decl: dict[str, Any], registry: Registry
) -> None:
    registry.provide(get_database, scope=Scope.NODE)
    registry.provide(get_user_service, scope=Scope.NODE)

    node = ToolNode.from_dict(multi_dep_tool_decl, registry)
    node.set_func(tool_with_multiple_dependencies)

    tool_call = ToolCall.model_validate(
        {
            "name": "multi_dep_tool",
            "args": {"action": "users"},
            "id": "call_456",
            "type": "tool_call",
        }
    )

    result = asyncio.run(node.invoke(tool_call, _make_execution_context(node)))

    assert isinstance(result, ToolMessage)
    assert "User(123) from test_db" in result.content
    assert "DB[test_db] executed: SELECT * FROM users" in result.content
    assert result.tool_call_id == "call_456"


def test_mixed_parameters_with_from_liman(
    mixed_tool_decl: dict[str, Any], registry: Registry
) -> None:
    registry.provide(get_database, scope=Scope.NODE)

    node = ToolNode.from_dict(mixed_tool_decl, registry)
    node.set_func(tool_mixed_params)

    tool_call = ToolCall.model_validate(
        {
            "name": "mixed_tool",
            "args": {"message": "test", "count": 3},
            "id": "call_789",
            "type": "tool_call",
        }
    )

    result = asyncio.run(node.invoke(tool_call, _make_execution_context(node)))

    assert isinstance(result, ToolMessage)
    assert "Inserted 3 records into test_db" in result.content
    assert result.tool_call_id == "call_789"


def test_from_liman_without_registry_provide_fails(
    from_liman_tool_decl: dict[str, Any], registry: Registry
) -> None:
    node = ToolNode.from_dict(from_liman_tool_decl, registry)
    node.set_func(tool_with_unprovided_dependency)

    tool_call = ToolCall.model_validate(
        {
            "name": "from_liman_tool",
            "args": {"message": "test"},
            "id": "call_error",
            "type": "tool_call",
        }
    )

    result = asyncio.run(node.invoke(tool_call, _make_execution_context(node)))

    assert isinstance(result, ToolMessage)
    assert "Cannot find factory" in result.content


def test_missing_required_param_with_from_liman(
    from_liman_tool_decl: dict[str, Any], registry: Registry
) -> None:
    registry.provide(get_database, scope=Scope.NODE)

    node = ToolNode.from_dict(from_liman_tool_decl, registry)
    node.set_func(tool_with_from_liman_db)

    tool_call = ToolCall.model_validate(
        {
            "name": "from_liman_tool",
            "args": {},
            "id": "call_error",
            "type": "tool_call",
        }
    )

    with pytest.raises(ValueError, match="Required parameter is missing: 'message'"):
        asyncio.run(node.invoke(tool_call, _make_execution_context(node)))
