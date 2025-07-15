from jsonschema_path.typing import Schema

from liman_openapi.schemas import Endpoint, Ref


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
