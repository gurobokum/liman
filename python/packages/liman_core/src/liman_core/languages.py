from typing import Annotated, Any, Generic, Literal, TypeGuard, TypeVar, get_args

from pydantic import BaseModel, BeforeValidator, ValidationInfo

from liman_core.errors import LimanError

LANGUAGE_CODES = get_args("LanguageCode")
LanguageCode = Literal["en", "ru", "zh", "fr", "de", "es", "it", "pt", "ja", "ko"]


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


type LocalizedValue = Annotated[
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
