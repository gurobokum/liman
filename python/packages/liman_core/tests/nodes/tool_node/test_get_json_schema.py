from typing import Any

import pytest

from liman_core.errors import InvalidSpecError
from liman_core.languages import LanguageCode
from liman_core.nodes.tool_node.node import ToolNode
from liman_core.registry import Registry


def make_tool_node(
    data: dict[str, Any],
    registry: Registry | None = None,
    default_lang: LanguageCode = "en",
    fallback_lang: LanguageCode = "en",
) -> ToolNode:
    if registry is None:
        registry = Registry()
    return ToolNode.from_dict(
        data,
        registry,
        default_lang=default_lang,
        fallback_lang=fallback_lang,
    )


def test_get_json_schema_basic() -> None:
    decl = {
        "kind": "ToolNode",
        "name": "test_tool_json",
        "description": {"en": "desc", "ru": "описание"},
        "func": "lib.tools.test_func",
        "arguments": [
            {"name": "foo", "type": "string", "description": {"en": "desc foo"}},
            {"name": "bar", "type": "number", "description": {"en": "desc bar"}},
        ],
    }
    expected_schema = {
        "type": "function",
        "function": {
            "name": "test_tool_json",
            "description": "desc",
            "parameters": {
                "type": "object",
                "properties": {
                    "foo": {
                        "type": "string",
                        "description": "desc foo",
                    },
                    "bar": {
                        "type": "number",
                        "description": "desc bar",
                    },
                },
                "required": ["foo", "bar"],
            },
        },
    }
    node = make_tool_node(decl)
    schema = node.get_json_schema("en")

    assert expected_schema == schema


def test_get_json_schema_fallback_lang() -> None:
    decl = {
        "kind": "ToolNode",
        "name": "test_tool_json2",
        "description": {"ru": "описание"},
        "func": "lib.tools.test_func",
        "arguments": [],
    }
    expected_schema = {
        "type": "function",
        "function": {
            "name": "test_tool_json2",
            "description": "описание",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }

    node = make_tool_node(decl, default_lang="en", fallback_lang="ru")
    schema = node.get_json_schema("en")
    assert expected_schema == schema


def test_get_json_schema_missing_description() -> None:
    decl = {
        "kind": "ToolNode",
        "name": "test_tool_json3",
        "description": {},
        "func": "lib.tools.test_func",
        "arguments": [],
    }

    node = make_tool_node(decl)
    with pytest.raises(InvalidSpecError, match="Spec doesn't have a description"):
        node.get_json_schema("en")


def test_get_json_schema_empty_arguments() -> None:
    decl = {
        "kind": "ToolNode",
        "name": "test_tool_json4",
        "description": {"en": "desc"},
        "func": "lib.tools.test_func",
        # arguments omitted
    }
    expected_schema = {
        "type": "function",
        "function": {
            "name": "test_tool_json4",
            "description": "desc",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }

    node = make_tool_node(decl)
    schema = node.get_json_schema("en")
    assert expected_schema == schema
