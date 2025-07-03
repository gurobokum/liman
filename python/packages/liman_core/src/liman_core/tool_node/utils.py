from typing import TypedDict

from liman_core.errors import InvalidSpecError
from liman_core.languages import (
    LanguageCode,
    LocalizationError,
    flatten_dict,
    get_localized_value,
)
from liman_core.tool_node.schemas import ToolArgument


class ToolArgumentJSONSchema(TypedDict):
    """
    TypedDict for JSON Schema representation of a tool argument.
    """

    type: str
    description: str


def tool_arg_to_jsonschema(
    spec: ToolArgument,
    default_lang: LanguageCode,
    fallback_lang: LanguageCode,
) -> dict[str, ToolArgumentJSONSchema]:
    """
    Convert a tool specification to JSON Schema format.

    Args:
        spec (ToolArgument): The tool specification model.

    Returns:
        dict[str, Any]: The JSON Schema representation of the tool specification.
    """
    name = spec.name
    try:
        desc_bundle = spec.description
        desc = get_localized_value(desc_bundle, default_lang, fallback_lang)
    except LocalizationError as e:
        raise InvalidSpecError(f"Invalid description in tool specification: {e}") from e

    if isinstance(desc, dict):
        desc_str = flatten_dict(desc)
    elif isinstance(desc, str):
        desc_str = desc
    else:
        raise InvalidSpecError(
            f"Invalid description type in tool specification: {type(desc).__name__}"
        )

    type_ = spec.type
    match type_:
        case "string" | "number" | "boolean":
            # For primitive types, we can directly use the type as a string
            ...
        case "str":
            type_ = "string"
        case "int":
            type_ = "number"
        case "float":
            type_ = "number"
        case "bool":
            type_ = "boolean"
        case "object":
            raise NotImplementedError("Object type is not supported yet.")
        case "array":
            raise NotImplementedError("Array type is not supported yet.")
        case _:
            raise InvalidSpecError(f"Unsupported type in tool specification: {type_}")

    return {name: ToolArgumentJSONSchema(description=desc_str, type=type_)}
