from liman_openapi import load_openapi


def test_load_openapi() -> None:
    test_schema = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
    }

    schema = load_openapi(test_schema)
    assert schema == test_schema


def test_load_openapi_with_endpoints() -> None:
    test_schema_with_endpoints = {
        "openapi": "3.0.0",
        "info": {"title": "Test API with Endpoints", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "summary": "Test endpoint",
                    "responses": {"200": {"description": "Successful response"}},
                }
            }
        },
    }

    schema = load_openapi(test_schema_with_endpoints)
    assert schema == test_schema_with_endpoints


def test_load_openapi_from_file_path() -> None:
    schema = load_openapi("./tests/data/simple_schema.yaml")
    assert schema["info"]["title"] == "Test API from File"
    assert "/test" in schema["paths"]
