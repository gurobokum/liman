from typing import Any

from liman_core.errors import InvalidSpecError
from liman_core.languages import LanguageCode, LocalizationError, get_localized_value
from liman_core.tool_node.schemas import ToolArgument


def tool_arg_to_jsonschema(
    spec: ToolArgument,
    default_lang: LanguageCode,
    fallback_lang: LanguageCode,
    optional: bool = False,
) -> dict[str, Any]:
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

    type_ = spec.type
    arg = {
        "name": name,
        "description": desc,
        "optional": optional,
    }
    match type_:
        case "string" | "number" | "boolean":
            arg["type"] = type_
        case "object":
            raise NotImplementedError("Object type is not supported yet.")
        case "array":
            raise NotImplementedError("Array type is not supported yet.")
        case _:
            raise InvalidSpecError(f"Unsupported type in tool specification: {type_}")
    return arg
