from typing import (
    Annotated,
    Any,
    Generic,
    Literal,
    TypeAlias,
    TypeGuard,
    TypeVar,
    get_args,
)

from pydantic import BaseModel, BeforeValidator, ValidationInfo

from liman_core.errors import LimanError

LANGUAGE_CODES = get_args("LanguageCode")
LanguageCode = Literal["en", "ru", "zh", "fr", "de", "es", "it", "pt", "ja", "ko"]


class LocalizationError(LimanError):
    """Base class for localization-related errors."""

    code = "localization_error"


def is_valid_language_code(code: str) -> TypeGuard[LanguageCode]:
    return code in get_args(LanguageCode)


T = TypeVar("T", bound="BaseModel")


def validate_localized_value(
    value: dict[str, Any] | str, info: ValidationInfo
) -> dict[LanguageCode, Any]:
    """
    Validate and normalize a localized value to ensure it has the correct structure.
    If the value is a string, it will be converted to a dictionary with the default language.
    """
    if isinstance(value, str):
        # If the value is a string, wrap it in a dictionary with the default language
        default_lang: LanguageCode = "en"
        if info.context and "default_lang" in info.context:
            default_lang = info.context["default_lang"]
        return {default_lang: value}
    return normalize_dict(value)


LocalizedValue: TypeAlias = Annotated[
    dict[LanguageCode, Any], BeforeValidator(validate_localized_value)
]


class LanguagesBundle(BaseModel, Generic[T]):
    """
    Represents a bundle of prompts for different languages.
    Each key is a language code (e.g., 'en', 'ru') and the value is the prompt text.
    """

    fallback_lang: LanguageCode = "en"

    en: T | None = None
    ru: T | None = None
    zh: T | None = None
    fr: T | None = None
    de: T | None = None
    it: T | None = None
    pt: T | None = None
    ja: T | None = None
    ko: T | None = None


def normalize_dict(
    data: dict[str, Any],
    default_lang: LanguageCode = "en",
) -> dict[LanguageCode, dict[str, Any] | str]:
    """
    Normalize a nested dictionary to have top-level language keys.
    Each value under the language keys will be a flattened dict of keys from different levels.

    Implementation Note:
      - Use pre-order DFS traversal
      - Detect language keys (e.g. "en", "ru") at any level.
      - Accumulate the full key path to place values in the final structure under the correct lang.
      - Treat non-language values as belonging to a default language (e.g. "en").
    """
    if not data:
        return {default_lang: ""}

    result: dict[LanguageCode, dict[str, Any] | str] = {}

    stack: list[tuple[LanguageCode | None, str, Any, list[str]]]
    stack = [(None, k, v, []) for k, v in data.items()]

    while stack:
        current_lang, key, value, path = stack.pop()
        if is_valid_language_code(key):
            current_lang = key
            sub_path = path
        else:
            sub_path = path + [key]

        if not current_lang:
            current_lang = default_lang

        if len(sub_path) == 0 and isinstance(value, str):
            # If the value is a string on the top level
            result[current_lang] = value
            continue

        d = result.setdefault(current_lang, {})
        if isinstance(d, str):
            raise LimanError(
                f"Expected a dict for language '{current_lang}' but got a string instead."
            )

        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                stack.append((current_lang, sub_key, sub_value, sub_path))
            continue

        for p in sub_path[:-1]:
            d = d.setdefault(p, {})
            if not isinstance(d, dict):
                raise LimanError(
                    f"Expected a dict at path {'.'.join(sub_path)} but got {type(d).__name__}"
                )
        d[sub_path[-1]] = value

    return dict(result)


def get_localized_value(
    data: dict[LanguageCode, Any],
    lang: LanguageCode,
    fallback_lang: LanguageCode = "en",
) -> Any:
    """
    Get a localized value from a dictionary of localized values.
    If the specified language is not available, fallback to the fallback language.
    """
    if lang in data:
        return data[lang]
    if fallback_lang in data:
        return data[fallback_lang]
    raise LocalizationError(
        f"No value found for language '{lang}' or fallback '{fallback_lang}'."
    )


def flatten_dict(
    data: dict[str, Any],
    prefix: str = "",
) -> str:
    """
    Flatten a dictionary with language keys into a single string in the format "path: value".
    Each path is a dot-separated string representing the hierarchy of keys.

    ```json
    {

    "user": {
        "profile": {
            "name": "Alice",
            "age": 30
        },
        "contact": {
            "email": "alice@example.com"
        }
    },
    "product": "Laptop"
    }
    ```json

    becomes:

    ```text
    user.profile.name: Alice
    user.profile.age: 30
    user.contact.email: alice@example.com
    product: Laptop
    ```
    """
    items = []
    output = []
    for k, v in data.items():
        key = f"{prefix}.{k}" if prefix else k

        if isinstance(v, dict):
            output.append(flatten_dict(v, key))
        else:
            items.append((key, v))

    output.append("\n".join(f"{k}: {v}" for k, v in items))
    return "\n".join(output)
