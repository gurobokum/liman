from typing import Generic, Literal, TypeGuard, TypeVar, get_args

from pydantic import BaseModel

LANGUAGE_CODES = get_args("LanguageCode")
LanguageCode = Literal["en", "ru", "zh", "fr", "de", "es", "it", "pt", "ja", "ko"]


def is_valid_language_code(code: str) -> TypeGuard[LanguageCode]:
    return code in get_args(LanguageCode)


T = TypeVar("T", bound="BaseModel")


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
