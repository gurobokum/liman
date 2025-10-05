from jsonschema_path.typing import Schema

from liman_openapi.parse import parse_security_schemes
from liman_openapi.schemas.security import HTTPSecurityScheme


def test_parse_security_schemes_empty() -> None:
    schema: Schema = {"components": {"securitySchemes": {}}}
    schemes = parse_security_schemes(schema)
    assert schemes == []


def test_parse_security_schemes(complex_openapi_schema: Schema) -> None:
    schemes = parse_security_schemes(complex_openapi_schema)

    assert len(schemes) == 1
    assert isinstance(schemes[0], HTTPSecurityScheme)
    assert schemes[0].type_ == "http"
    assert schemes[0].scheme == "bearer"
    assert schemes[0].bearer_format == "JWT"
