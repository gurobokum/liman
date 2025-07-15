from rich import print as rich_print

from liman_openapi import load_openapi
from liman_openapi.parse import parse_endpoints, parse_refs


def test_parse_components() -> None:
    schema = load_openapi("./tests/data/schema.yaml")
    refs = parse_refs(schema.spec.contents())
    endpoints = parse_endpoints(schema.spec.contents())
    print(refs)
    rich_print(endpoints)
