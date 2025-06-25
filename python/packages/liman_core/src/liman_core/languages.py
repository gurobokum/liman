from typing import Any, Generic, Literal, TypeGuard, TypeVar, get_args

from pydantic import BaseModel

LANGUAGE_CODES = get_args("LanguageCode")
LanguageCode = Literal["en", "ru", "zh", "fr", "de", "es", "it", "pt", "ja", "ko"]


def is_valid_language_code(code: str) -> TypeGuard[LanguageCode]:
    return code in get_args(LanguageCode)


T = TypeVar("T", bound="BaseModel")

type LocalizedValue = dict[str, Any] | str


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
) -> dict[LanguageCode, Any]:
    """
    Normalize a nested dictionary to have top-level language keys.
    Each value under the language keys will be a flattened dict of keys from different levels.

    Implementation Note:
      - Use pre-order DFS traversal
      - Detect language keys (e.g. "en", "ru") at any level.
      - Accumulate the full key path to place values in the final structure under the correct lang.
      - Treat non-language values as belonging to a default language (e.g. "en").
    """
    result: dict[LanguageCode, dict[str, Any]] = {}

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

        d = result.setdefault(current_lang, {})
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                stack.append((current_lang, sub_key, sub_value, sub_path))
            continue

        for p in sub_path[:-1]:
            d = d.setdefault(p, {})
        d[sub_path[-1]] = value

    return dict(result)
