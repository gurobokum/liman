from jsonschema_path.typing import Schema

from liman_openapi.parse import parse_security_schemes
from liman_openapi.schemas.security import ApiKeySecurityScheme, HTTPSecurityScheme


def test_parse_security_schemes_empty() -> None:
    schema: Schema = {"components": {"securitySchemes": {}}}
    schemes = parse_security_schemes(schema)
    assert schemes == {}


def test_parse_security_schemes_no_components() -> None:
    schema: Schema = {}
    schemes = parse_security_schemes(schema)
    assert schemes == {}


def test_parse_security_schemes(complex_openapi_schema: Schema) -> None:
    schemes = parse_security_schemes(complex_openapi_schema)

    assert len(schemes) == 1
    assert "bearerAuth" in schemes
    scheme = schemes["bearerAuth"]
    assert isinstance(scheme, HTTPSecurityScheme)
    assert scheme.type_ == "http"
    assert scheme.scheme == "bearer"
    assert scheme.bearer_format == "JWT"


def test_parse_security_schemes_api_key() -> None:
    schema: Schema = {
        "components": {
            "securitySchemes": {
                "apiKey": {
                    "type": "apiKey",
                    "name": "X-API-Key",
                    "in": "header",
                }
            }
        }
    }
    schemes = parse_security_schemes(schema)

    assert len(schemes) == 1
    assert "apiKey" in schemes
    scheme = schemes["apiKey"]
    assert isinstance(scheme, ApiKeySecurityScheme)
    assert scheme.name == "X-API-Key"
    assert scheme.in_ == "header"


def test_parse_security_schemes_unsupported_type_is_skipped() -> None:
    schema: Schema = {
        "components": {
            "securitySchemes": {
                "oauth2": {"type": "oauth2", "flows": {}},
                "bearerAuth": {"type": "http", "scheme": "bearer"},
            }
        }
    }
    schemes = parse_security_schemes(schema)

    assert len(schemes) == 1
    assert "bearerAuth" in schemes
    assert "oauth2" not in schemes


def test_parse_security_schemes_multiple() -> None:
    schema: Schema = {
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer"},
                "apiKey": {"type": "apiKey", "name": "X-API-Key", "in": "header"},
            }
        }
    }
    schemes = parse_security_schemes(schema)

    assert len(schemes) == 2
    assert isinstance(schemes["bearerAuth"], HTTPSecurityScheme)
    assert isinstance(schemes["apiKey"], ApiKeySecurityScheme)
