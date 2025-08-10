import pytest

from liman_core.errors import InvalidSpecError
from liman_core.nodes.tool_node.schemas import ToolArgument
from liman_core.nodes.tool_node.utils import tool_arg_to_jsonschema


def test_tool_arg_to_jsonschema_string() -> None:
    arg = ToolArgument(
        name="foo",
        type="string",
        description={"en": "A string argument", "ru": "Строковый аргумент"},
    )

    result = tool_arg_to_jsonschema(arg, default_lang="en", fallback_lang="ru")
    assert result == {
        "foo": {
            "type": "string",
            "description": "A string argument",
        }
    }


def test_tool_arg_to_jsonschema_number() -> None:
    arg = ToolArgument(
        name="bar",
        type="number",
        description={"en": "A number argument"},
    )

    result = tool_arg_to_jsonschema(arg, default_lang="en", fallback_lang="ru")
    schema = result["bar"]
    assert schema["type"] == "number"
    assert schema["description"] == "A number argument"


def test_tool_arg_to_jsonschema_boolean() -> None:
    arg = ToolArgument(
        name="baz",
        type="boolean",
        description={"en": "A boolean argument"},
    )

    result = tool_arg_to_jsonschema(arg, default_lang="en", fallback_lang="ru")
    schema = result["baz"]
    assert schema["type"] == "boolean"
    assert schema["description"] == "A boolean argument"


def test_tool_arg_to_jsonschema_invalid_type() -> None:
    arg = ToolArgument(
        name="bad",
        type="invalid_type",
        description={"en": "Invalid type"},
    )
    with pytest.raises(
        InvalidSpecError, match="Unsupported type in tool specification"
    ):
        tool_arg_to_jsonschema(arg, default_lang="en", fallback_lang="ru")


def test_tool_arg_to_jsonschema_localization_error() -> None:
    arg = ToolArgument(
        name="foo",
        type="string",
        description={"en": "desc"},
    )

    with pytest.raises(
        InvalidSpecError,
        match="Invalid description in tool specification",
    ):
        tool_arg_to_jsonschema(arg, default_lang="fr", fallback_lang="fr")
