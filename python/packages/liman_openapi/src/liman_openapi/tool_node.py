import logging
from typing import TypeVar

from liman_core.tool_node.node import ToolNode
from openapi_core import OpenAPI

from liman_openapi.operation import OpenAPIOperation
from liman_openapi.parse import parse_endpoints, parse_refs

logger = logging.getLogger(__name__)


def create_tool_nodes(
    openapi_spec: OpenAPI, prefix: str = "OpenAPI", is_async: bool = False
) -> list[ToolNode]:
    """
    Generate ToolNode instances based on OpenAPI endpoints.

    Args:
        openapi_spec (dict): The OpenAPI specification.

    Returns:
        List[ToolNode]: A list of ToolNode instances.
    """
    nodes = []
    spec_content = openapi_spec.spec.content()
    endpoints = parse_endpoints(spec_content)
    refs = parse_refs(spec_content)

    base_url = None
    servers = spec_content.get("servers", [])
    if servers:
        base_url = servers[0].get("url")

    for endpoint in endpoints:
        name = f"{prefix}__{endpoint.operation_id}"
        node_declaration = {
            "kind": "ToolNode",
            "name": name,
            "description": endpoint.summary,
            "arguments": endpoint.get_tool_arguments_spec(),
        }

        node = ToolNode(name=name, declaration=node_declaration)
        impl_func = OpenAPIOperation(endpoint, refs, base_url=base_url)
        node.set_func(impl_func)
        nodes.append(node)

    return nodes


R = TypeVar("R")
