from typing import Any

import pytest
from pydantic import ValidationError

from liman_openapi.schemas import (
    Endpoint,
    Parameter,
    ParameterSchema,
    Property,
    Ref,
    RequestBody,
    RequestBodySchema,
    Response,
)


def test_parameter_schema_minimal() -> None:
    data = {"type": "string"}
    schema = ParameterSchema.model_validate(data)

    assert schema.type_ == "string"
    assert schema.format_ is None
    assert schema.title is None


def test_parameter_schema_with_format() -> None:
    data = {"type": "string", "format": "email", "title": "Email"}
    schema = ParameterSchema.model_validate(data)

    assert schema.type_ == "string"
    assert schema.format_ == "email"
    assert schema.title == "Email"


def test_parameter_minimal(parameter_data: dict[str, Any]) -> None:
    param = Parameter.model_validate(parameter_data)

    assert param.name == "test_param"
    assert param.description == "Test parameter description"
    assert param.in_ == "query"
    assert param.required is True
    assert param.schema_.type_ == "string"


def test_parameter_get_json_schema(parameter_data: dict[str, Any]) -> None:
    param = Parameter.model_validate(parameter_data)
    json_schema = param.get_json_schema()
    expected = {"name": "test_param", "description": "Test parameter description"}

    assert json_schema == expected


def test_parameter_get_tool_argument_spec(parameter_data: dict[str, Any]) -> None:
    param = Parameter.model_validate(parameter_data)
    spec = param.get_tool_argument_spec()
    expected = {
        "name": "test_param",
        "type": "string",
        "description": "Test parameter description",
        "optional": False,
    }

    assert spec == expected


def test_parameter_optional() -> None:
    data = {
        "name": "optional_param",
        "description": "Optional parameter",
        "in": "query",
        "required": False,
        "schema": {"type": "string"},
    }
    param = Parameter.model_validate(data)
    spec = param.get_tool_argument_spec()

    assert spec["optional"] is True


def test_request_body_minimal() -> None:
    data = {"content": {"application/json": {"schema": {"type": "string"}}}}
    body = RequestBody.model_validate(data)

    assert body.required is False
    assert "application/json" in body.content
    schema = body.content["application/json"]["schema"]
    assert schema.content_type == "application/json"
    assert schema.type_ == "string"


def test_request_body_required() -> None:
    data = {
        "required": True,
        "content": {"application/json": {"schema": {"type": "string"}}},
    }
    body = RequestBody.model_validate(data)

    assert body.required is True


def test_request_body_with_ref() -> None:
    data = {
        "content": {
            "application/json": {"schema": {"$ref": "#/components/schemas/User"}}
        }
    }
    body = RequestBody.model_validate(data)
    schema = body.content["application/json"]["schema"]

    assert isinstance(schema, RequestBodySchema)
    assert schema.ref == "#/components/schemas/User"
    assert schema.content_type == "application/json"


def test_response_minimal() -> None:
    data = {
        "description": "Success response",
        "status_code": "200",
        "content": {"application/json": {"schema": {"type": "string"}}},
    }
    response = Response.model_validate(data)

    assert response.description == "Success response"
    assert "application/json" in response.content
    schema = response.content["application/json"]["schema"]
    assert schema.content_type == "application/json"
    assert schema.type_ == "string"


def test_response_with_status_code() -> None:
    data = {
        "status_code": "201",
        "description": "Created",
        "content": {"application/json": {"schema": {"type": "string"}}},
    }
    response = Response.model_validate(data)

    assert response.status_code == "201"


def test_endpoint_minimal(endpoint_data: dict[str, Any]) -> None:
    endpoint = Endpoint.model_validate(endpoint_data)

    assert endpoint.operation_id == "test_operation"
    assert endpoint.summary == "Test operation summary"
    assert endpoint.method == "GET"
    assert endpoint.path == "/test/{id}"
    assert len(endpoint.parameters) == 1
    assert endpoint.request_body is None
    assert "200" in endpoint.responses


def test_endpoint_get_tool_arguments_spec(endpoint_data: dict[str, Any]) -> None:
    endpoint = Endpoint.model_validate(endpoint_data)
    spec = endpoint.get_tool_arguments_spec()

    assert spec is not None
    assert len(spec) == 1
    assert spec[0]["name"] == "id"
    assert spec[0]["type"] == "string"


def test_endpoint_no_parameters() -> None:
    data = {
        "operationId": "simple_op",
        "summary": "Simple operation",
        "method": "GET",
        "path": "/simple",
        "responses": {
            "200": {
                "description": "Success",
                "content": {"application/json": {"schema": {"type": "string"}}},
            }
        },
    }
    endpoint = Endpoint.model_validate(data)
    spec = endpoint.get_tool_arguments_spec()

    assert spec is None


def test_endpoint_with_request_body() -> None:
    data = {
        "operationId": "create_item",
        "summary": "Create item",
        "method": "POST",
        "path": "/items",
        "requestBody": {
            "required": True,
            "content": {"application/json": {"schema": {"type": "string"}}},
        },
        "responses": {
            "201": {
                "description": "Created",
                "content": {"application/json": {"schema": {"type": "string"}}},
            }
        },
    }
    endpoint = Endpoint.model_validate(data)

    assert endpoint.request_body is not None
    assert endpoint.request_body.required is True


def test_property_minimal() -> None:
    data = {"name": "test_prop", "type": "string"}
    prop = Property.model_validate(data)

    assert prop.name == "test_prop"
    assert prop.type_ == "string"
    assert prop.description is None
    assert prop.example is None


def test_property_with_details() -> None:
    data = {
        "name": "user_age",
        "type": "integer",
        "description": "User age in years",
        "example": 25,
    }
    prop = Property.model_validate(data)

    assert prop.name == "user_age"
    assert prop.type_ == "integer"
    assert prop.description == "User age in years"
    assert prop.example == 25


def test_ref_minimal(ref_data: dict[str, Any]) -> None:
    ref = Ref.model_validate(ref_data)

    assert ref.name == "TestRef"
    assert len(ref.properties) == 2
    assert "id" in ref.properties
    assert "name" in ref.properties
    assert ref.required == ["id"]


def test_ref_property_name_injection() -> None:
    data = {
        "name": "User",
        "properties": {"user_id": {"type": "string"}, "full_name": {"type": "string"}},
    }
    ref = Ref.model_validate(data)

    assert ref.properties["user_id"].name == "user_id"
    assert ref.properties["full_name"].name == "full_name"


def test_invalid_parameter_type() -> None:
    data = {
        "name": "bad_param",
        "description": "Bad parameter",
        "in": "query",
        "schema": {"type": "invalid_type"},
    }

    with pytest.raises(ValidationError):
        Parameter.model_validate(data)


def test_endpoint_status_code_injection() -> None:
    data = {
        "operationId": "test_op",
        "summary": "Test",
        "method": "GET",
        "path": "/test",
        "responses": {
            "200": {
                "description": "OK",
                "content": {"application/json": {"schema": {"type": "string"}}},
            },
            "404": {
                "description": "Not Found",
                "content": {"application/json": {"schema": {"type": "string"}}},
            },
        },
    }
    endpoint = Endpoint.model_validate(data)

    assert endpoint.responses["200"].status_code == "200"
    assert endpoint.responses["404"].status_code == "404"
