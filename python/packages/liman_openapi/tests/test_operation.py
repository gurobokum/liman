from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from liman_openapi.operation import OpenAPIOperation
from liman_openapi.schemas import Endpoint


@pytest.fixture
def simple_endpoint() -> Endpoint:
    return Endpoint.model_validate(
        {
            "operationId": "get_user",
            "summary": "Get user by ID",
            "method": "GET",
            "path": "/users/{user_id}",
            "parameters": [
                {
                    "name": "user_id",
                    "in": "path",
                    "required": True,
                    "description": "User ID",
                    "schema": {"type": "string"},
                }
            ],
            "responses": {
                "200": {
                    "description": "User found",
                    "content": {"application/json": {"schema": {"type": "string"}}},
                }
            },
        }
    )


@pytest.fixture
def endpoint_with_query_params() -> Endpoint:
    return Endpoint.model_validate(
        {
            "operationId": "list_users",
            "summary": "List users",
            "method": "GET",
            "path": "/users",
            "parameters": [
                {
                    "name": "limit",
                    "in": "query",
                    "required": False,
                    "description": "Number of users to return",
                    "schema": {"type": "integer"},
                },
                {
                    "name": "offset",
                    "in": "query",
                    "required": False,
                    "description": "Number of users to skip",
                    "schema": {"type": "integer"},
                },
            ],
            "responses": {
                "200": {
                    "description": "Users list",
                    "content": {"application/json": {"schema": {"type": "array"}}},
                }
            },
        }
    )


@pytest.fixture
def endpoint_with_request_body() -> Endpoint:
    return Endpoint.model_validate(
        {
            "operationId": "create_user",
            "summary": "Create user",
            "method": "POST",
            "path": "/users",
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": {"type": "object"}}},
            },
            "responses": {
                "201": {
                    "description": "User created",
                    "content": {"application/json": {"schema": {"type": "object"}}},
                }
            },
        }
    )


@pytest.fixture
def mock_endpoint() -> Endpoint:
    mock = Mock(spec=Endpoint)
    mock.parameters = []
    mock.request_body = None
    return mock


def test_operation_init(simple_endpoint: Endpoint) -> None:
    operation = OpenAPIOperation(simple_endpoint)
    assert operation.endpoint == simple_endpoint
    assert operation.refs is None
    assert operation.base_url is None


def test_operation_init_with_base_url(simple_endpoint: Endpoint) -> None:
    base_url = "https://api.example.com"
    operation = OpenAPIOperation(simple_endpoint, base_url=base_url)
    assert operation.base_url == base_url


def test_operation_repr(simple_endpoint: Endpoint) -> None:
    operation = OpenAPIOperation(simple_endpoint)
    repr_str = repr(operation)
    assert "liman_openapi.gen.id_" in repr_str
    assert "get_user" in repr_str


def test_build_url_and_params_path_parameter(simple_endpoint: Endpoint) -> None:
    operation = OpenAPIOperation(simple_endpoint, base_url="https://api.example.com")
    url, query_params, headers, json_data = operation._build_url_and_params(
        user_id="123"
    )

    assert url == "https://api.example.com/users/123"
    assert query_params == {}
    assert headers == {}
    assert json_data is None


def test_build_url_and_params_query_parameters(
    endpoint_with_query_params: Endpoint,
) -> None:
    operation = OpenAPIOperation(endpoint_with_query_params)
    url, query_params, headers, json_data = operation._build_url_and_params(
        limit=10, offset=20
    )

    assert url == "/users"
    assert query_params == {"limit": 10, "offset": 20}
    assert headers == {}
    assert json_data is None


def test_build_url_and_params_missing_required(simple_endpoint: Endpoint) -> None:
    operation = OpenAPIOperation(simple_endpoint)

    with pytest.raises(ValueError, match="Required parameter is missing: 'user_id'"):
        operation._build_url_and_params()


def test_build_url_and_params_with_request_body(
    endpoint_with_request_body: Endpoint,
) -> None:
    operation = OpenAPIOperation(endpoint_with_request_body)
    body_data = {"name": "John", "email": "john@example.com"}

    url, query_params, headers, json_data = operation._build_url_and_params(
        __request_body__=body_data
    )

    assert url == "/users"
    assert query_params == {}
    assert headers == {"Content-Type": "application/json"}
    assert json_data == body_data


def test_build_url_and_params_missing_required_body(
    endpoint_with_request_body: Endpoint,
) -> None:
    operation = OpenAPIOperation(endpoint_with_request_body)

    with pytest.raises(
        ValueError, match="Required request body is missing: '__request_body__'"
    ):
        operation._build_url_and_params()


def test_build_url_and_params_header_parameter() -> None:
    endpoint = Endpoint.model_validate(
        {
            "operationId": "auth_test",
            "summary": "Test with auth header",
            "method": "GET",
            "path": "/protected",
            "parameters": [
                {
                    "name": "Authorization",
                    "in": "header",
                    "required": True,
                    "description": "Auth token",
                    "schema": {"type": "string"},
                }
            ],
            "responses": {
                "200": {
                    "description": "OK",
                    "content": {"application/json": {"schema": {"type": "string"}}},
                }
            },
        }
    )

    operation = OpenAPIOperation(endpoint)
    url, query_params, headers, json_data = operation._build_url_and_params(
        Authorization="Bearer token123"
    )

    assert url == "/protected"
    assert query_params == {}
    assert headers == {"Authorization": "Bearer token123"}
    assert json_data is None


def test_parse_response_json(mock_endpoint: Endpoint) -> None:
    mock_response = Mock(spec=httpx.Response)
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"id": "123", "name": "John"}
    mock_response.parameters = []

    operation = OpenAPIOperation(mock_endpoint)
    result = operation._parse_response(mock_response)

    assert result == {"id": "123", "name": "John"}
    mock_response.json.assert_called_once()


def test_parse_response_text(mock_endpoint: Endpoint) -> None:
    mock_response = Mock(spec=httpx.Response)
    mock_response.headers = {"content-type": "text/plain"}
    mock_response.text = "Hello World"

    operation = OpenAPIOperation(mock_endpoint)
    result = operation._parse_response(mock_response)

    assert result == "Hello World"


def test_parse_response_image(mock_endpoint: Endpoint) -> None:
    mock_response = Mock(spec=httpx.Response)
    mock_response.headers = {"content-type": "image/png"}
    mock_response.content = b"fake_image_data"

    operation = OpenAPIOperation(mock_endpoint)
    result = operation._parse_response(mock_response)

    assert result == b"fake_image_data"


def test_parse_response_octet_stream(mock_endpoint: Endpoint) -> None:
    mock_response = Mock(spec=httpx.Response)
    mock_response.headers = {"content-type": "application/octet-stream"}
    mock_response.content = b"binary_data"

    operation = OpenAPIOperation(mock_endpoint)
    result = operation._parse_response(mock_response)

    assert result == b"binary_data"


def test_parse_response_unsupported_content_type(mock_endpoint: Endpoint) -> None:
    mock_response = Mock(spec=httpx.Response)
    mock_response.headers = {"content-type": "application/xml"}

    operation = OpenAPIOperation(mock_endpoint)

    with pytest.raises(ValueError, match="Unsupported content type: application/xml"):
        operation._parse_response(mock_response)


def test_parse_response_missing_content_type(mock_endpoint: Endpoint) -> None:
    mock_response = Mock(spec=httpx.Response)
    mock_response.headers = {}

    operation = OpenAPIOperation(mock_endpoint)

    with pytest.raises(ValueError, match="Unsupported content type: "):
        operation._parse_response(mock_response)


@patch("liman_openapi.operation.httpx.AsyncClient")
async def test_request_success(
    mock_client_class: AsyncMock, simple_endpoint: Endpoint
) -> None:
    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client

    mock_response = Mock(spec=httpx.Response)
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"id": "123"}
    mock_client.request.return_value = mock_response

    operation = OpenAPIOperation(simple_endpoint, base_url="https://api.example.com")
    result = await operation._request(user_id="123")

    assert result == {"id": "123"}
    mock_client.request.assert_called_once_with(
        "GET", "https://api.example.com/users/123", params=None, headers={}, json=None
    )


@patch("liman_openapi.operation.httpx.AsyncClient")
async def test_request_http_error(
    mock_client_class: AsyncMock, simple_endpoint: Endpoint
) -> None:
    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client

    mock_response = Mock(spec=httpx.Response)
    mock_response.headers = {"content-type": "application/json"}
    mock_response.status_code = 404
    mock_response.text = "Not found"

    http_error = httpx.HTTPStatusError(
        "Not found", request=Mock(), response=mock_response
    )
    mock_client.request.side_effect = http_error

    operation = OpenAPIOperation(simple_endpoint)

    with pytest.raises(RuntimeError, match="HTTP error occurred: 404 Not found"):
        await operation._request(user_id="123")


async def test_request(simple_endpoint: Endpoint) -> None:
    operation = OpenAPIOperation(simple_endpoint)

    with patch.object(operation, "_request") as mock_request:
        mock_request.return_value = {"result": "success"}
        result = await operation(user_id="123")

        assert result == {"result": "success"}
        mock_request.assert_called_once_with(user_id="123")


@patch("liman_openapi.operation.httpx.AsyncClient")
async def test_request_error(
    mock_client_class: Mock, simple_endpoint: Endpoint
) -> None:
    mock_client = Mock()
    mock_client_class.return_value.__aenter__.return_value = mock_client

    request_error = httpx.RequestError("Connection failed")
    mock_client.request.side_effect = request_error

    operation = OpenAPIOperation(simple_endpoint)

    with pytest.raises(RuntimeError, match="Request error occurred: Connection failed"):
        await operation._request(user_id="123")
