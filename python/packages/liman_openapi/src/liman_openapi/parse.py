import logging

from jsonschema_path.typing import Schema

from liman_openapi.schemas import Endpoint, Ref
from liman_openapi.schemas.security import (
    ApiKeySecurityScheme,
    HTTPSecurityScheme,
    SecurityScheme,
)

logger = logging.getLogger(__name__)


def parse_refs(schema: Schema) -> dict[str, Ref]:
    """
    Parses components from an OpenAPI schema.
    """
    schemas = schema.get("components", {"schemas": {}}).get("schemas", {})
    components = {}
    for name, schema in schemas.items():
        components[name] = Ref.model_validate(
            {
                "name": name,
                **schema,
            }
        )
    return components


def parse_security_schemes(schema: Schema) -> list[SecurityScheme]:
    security_schemes = schema.get("components", {"securitySchemes": {}}).get(
        "securitySchemes", {}
    )

    schemes: list[SecurityScheme] = []
    for security_scheme in security_schemes.values():
        match security_scheme["type"]:
            case "http":
                schemes.append(HTTPSecurityScheme.model_validate(security_scheme))
            case "apiKey":
                schemes.append(ApiKeySecurityScheme.model_validate(security_scheme))
            case _:
                logger.warning(
                    f"Unsupported security scheme type: {security_scheme['type']}"
                )

    return schemes


def parse_endpoints(schema: Schema) -> list[Endpoint]:
    """
    Parses endpoints from an OpenAPI schema.
    """
    paths = schema.get("paths", {})
    endpoints = []
    for path, methods in paths.items():
        for method, details in methods.items():
            endpoints.append(
                Endpoint.model_validate(
                    {**details, "method": method.upper(), "path": path},
                )
            )
    return endpoints
