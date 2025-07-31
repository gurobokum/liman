import pytest
from jsonschema_path.typing import Schema


@pytest.fixture
def simple_openapi_schema() -> Schema:
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users/{user_id}": {
                "get": {
                    "operationId": "get_user",
                    "summary": "Get user by ID",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "description": "User identifier",
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "User found",
                            "content": {
                                "application/json": {"schema": {"type": "string"}}
                            },
                        }
                    },
                }
            }
        },
    }


@pytest.fixture
def complex_openapi_schema() -> Schema:
    return {
        "openapi": "3.0.0",
        "info": {"title": "Complex API", "version": "1.0.0"},
        "servers": [{"url": "https://api.example.com"}],
        "paths": {
            "/users": {
                "post": {
                    "operationId": "create_user",
                    "summary": "Create a new user",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "User created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            },
                        }
                    },
                }
            },
            "/users/{user_id}": {
                "get": {
                    "operationId": "get_user_by_id",
                    "summary": "Get user by ID",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "description": "User identifier",
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "include_posts",
                            "in": "query",
                            "required": False,
                            "description": "Include user posts",
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "User found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            },
                        }
                    },
                }
            },
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "required": ["name", "email"],
                    "properties": {
                        "id": {"type": "string", "description": "User ID"},
                        "name": {"type": "string", "description": "User name"},
                        "email": {"type": "string", "description": "User email"},
                    },
                }
            }
        },
    }


@pytest.fixture
def endpoint_data() -> Schema:
    """
    Sample endpoint data for testing Endpoint model.
    """
    return {
        "operationId": "test_operation",
        "summary": "Test operation summary",
        "method": "GET",
        "path": "/test/{id}",
        "parameters": [
            {
                "name": "id",
                "in": "path",
                "required": True,
                "description": "Test ID",
                "schema": {"type": "string"},
            }
        ],
        "responses": {
            "200": {
                "description": "Success",
                "content": {"application/json": {"schema": {"type": "string"}}},
            }
        },
    }


@pytest.fixture
def parameter_data() -> Schema:
    """
    Sample parameter data for testing Parameter model.
    """
    return {
        "name": "test_param",
        "description": "Test parameter description",
        "in": "query",
        "required": True,
        "schema": {"type": "string"},
    }


@pytest.fixture
def ref_data() -> Schema:
    """
    Sample reference data for testing Ref model.
    """
    return {
        "name": "TestRef",
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "ID field"},
            "name": {"type": "string", "description": "Name field"},
        },
        "required": ["id"],
    }
