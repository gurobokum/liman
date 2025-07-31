from jsonschema_path.typing import Schema

from liman_openapi.parse import parse_endpoints, parse_refs


def test_parse_refs_empty_schema() -> None:
    schema: Schema = {}
    refs = parse_refs(schema)
    assert refs == {}


def test_parse_refs_no_components() -> None:
    schema: Schema = {"paths": {}}
    refs = parse_refs(schema)
    assert refs == {}


def test_parse_refs_empty_components() -> None:
    schema: Schema = {"components": {"schemas": {}}}
    refs = parse_refs(schema)
    assert refs == {}


def test_parse_refs_single_component(complex_openapi_schema: Schema) -> None:
    refs = parse_refs(complex_openapi_schema)
    assert len(refs) == 1
    assert "User" in refs

    user_ref = refs["User"]
    assert user_ref.name == "User"
    assert len(user_ref.properties) == 3
    assert "id" in user_ref.properties
    assert "name" in user_ref.properties
    assert "email" in user_ref.properties
    assert user_ref.required == ["name", "email"]


def test_parse_refs_multiple_components() -> None:
    schema: Schema = {
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                    },
                },
                "Post": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                    },
                },
            }
        }
    }

    refs = parse_refs(schema)
    assert len(refs) == 2
    assert "User" in refs
    assert "Post" in refs

    assert refs["User"].name == "User"
    assert refs["Post"].name == "Post"


def test_parse_endpoints_empty_schema() -> None:
    schema: Schema = {}
    endpoints = parse_endpoints(schema)
    assert endpoints == []


def test_parse_endpoints_no_paths() -> None:
    schema: Schema = {"info": {"title": "Test"}}
    endpoints = parse_endpoints(schema)
    assert endpoints == []


def test_parse_endpoints_empty_paths() -> None:
    schema: Schema = {"paths": {}}
    endpoints = parse_endpoints(schema)
    assert endpoints == []


def test_parse_endpoints_single_endpoint(simple_openapi_schema: Schema) -> None:
    endpoints = parse_endpoints(simple_openapi_schema)
    assert len(endpoints) == 1

    endpoint = endpoints[0]
    assert endpoint.operation_id == "get_user"
    assert endpoint.summary == "Get user by ID"
    assert endpoint.method == "GET"
    assert endpoint.path == "/users/{user_id}"
    assert len(endpoint.parameters) == 1
    assert endpoint.parameters[0].name == "user_id"


def test_parse_endpoints_multiple_endpoints(
    complex_openapi_schema: Schema,
) -> None:
    endpoints = parse_endpoints(complex_openapi_schema)
    assert len(endpoints) == 2

    operation_ids = {ep.operation_id for ep in endpoints}
    assert operation_ids == {"create_user", "get_user_by_id"}

    get_endpoint = next(ep for ep in endpoints if ep.operation_id == "get_user_by_id")
    assert get_endpoint.method == "GET"
    assert get_endpoint.path == "/users/{user_id}"
    assert len(get_endpoint.parameters) == 2

    post_endpoint = next(ep for ep in endpoints if ep.operation_id == "create_user")
    assert post_endpoint.method == "POST"
    assert post_endpoint.path == "/users"
    assert post_endpoint.request_body is not None


def test_parse_endpoints_multiple_methods_same_path() -> None:
    schema: Schema = {
        "paths": {
            "/items/{id}": {
                "get": {
                    "operationId": "get_item",
                    "summary": "Get item",
                    "responses": {"200": {"description": "OK"}},
                },
                "put": {
                    "operationId": "update_item",
                    "summary": "Update item",
                    "responses": {"200": {"description": "OK"}},
                },
                "delete": {
                    "operationId": "delete_item",
                    "summary": "Delete item",
                    "responses": {"204": {"description": "No Content"}},
                },
            }
        }
    }

    endpoints = parse_endpoints(schema)
    assert len(endpoints) == 3

    methods = {ep.method for ep in endpoints}
    assert methods == {"GET", "PUT", "DELETE"}

    for endpoint in endpoints:
        assert endpoint.path == "/items/{id}"


def test_parse_endpoints_method_case_normalization() -> None:
    schema: Schema = {
        "paths": {
            "/test": {
                "get": {
                    "operationId": "get_test",
                    "summary": "Get test",
                    "responses": {"200": {"description": "OK"}},
                },
                "post": {
                    "operationId": "post_test",
                    "summary": "Post test",
                    "responses": {"201": {"description": "Created"}},
                },
            }
        }
    }

    endpoints = parse_endpoints(schema)
    assert len(endpoints) == 2

    for endpoint in endpoints:
        assert endpoint.method in ["GET", "POST"]


def test_parse_endpoints_with_parameters() -> None:
    schema: Schema = {
        "paths": {
            "/api/{version}/users": {
                "get": {
                    "operationId": "list_users",
                    "summary": "List users",
                    "parameters": [
                        {
                            "name": "version",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer"},
                        },
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            }
        }
    }

    endpoints = parse_endpoints(schema)
    assert len(endpoints) == 1

    endpoint = endpoints[0]
    assert len(endpoint.parameters) == 2

    path_param = next(p for p in endpoint.parameters if p.in_ == "path")
    assert path_param.name == "version"
    assert path_param.required is True

    query_param = next(p for p in endpoint.parameters if p.in_ == "query")
    assert query_param.name == "limit"
    assert query_param.required is False
