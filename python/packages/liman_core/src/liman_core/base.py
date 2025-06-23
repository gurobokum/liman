from typing import Any
from uuid import uuid4

from ruamel.yaml import YAML

from liman_core.errors import LimanError
from liman_core.languages import LanguageCode, is_valid_language_code


class BaseNode:
    __slots__ = (
        "id",
        "declaration",
        "yaml_path",
        "default_lang",
        "fallback_lang",
        "_compiled",
    )

    def __init__(
        self,
        *,
        declaration: dict[str, Any] | None = None,
        yaml_path: str | None = None,
        default_lang: str = "en",
        fallback_lang: str = "en",
    ) -> None:
        if not is_valid_language_code(default_lang):
            raise LimanError(f"Invalid default language code: {default_lang}")
        self.default_lang: LanguageCode = default_lang

        if not is_valid_language_code(fallback_lang):
            raise LimanError(f"Invalid fallback language code: {fallback_lang}")
        self.fallback_lang: LanguageCode = fallback_lang

        self.declaration = declaration
        self.yaml_path = yaml_path

        self.generate_id()
        self._compiled = False

    @classmethod
    def from_yaml(
        cls,
        yaml_data: dict[str, Any],
        *,
        default_lang: str = "en",
        fallback_lang: str = "en",
    ) -> "BaseNode":
        """
        Create a BaseNode instance from a YAML dictionary.

        Args:
            yaml_data (dict[str, Any]): Dictionary containing YAML data.

        Returns:
            BaseNode: An instance of BaseNode initialized with the YAML data.
        """
        return cls(
            declaration=yaml_data,
            default_lang=default_lang,
            fallback_lang=fallback_lang,
        )

    @classmethod
    def from_yaml_path(
        cls,
        yaml_path: str,
        *,
        default_lang: str = "en",
        fallback_lang: str = "en",
    ) -> "BaseNode":
        """
        Create a BaseNode instance from a YAML file.

        Args:
            yaml_path (str): Path to the YAML file.

        Returns:
            BaseNode: An instance of BaseNode initialized with the YAML data.
        """
        yaml_data = YAML().load(yaml_path).dict()
        return cls(
            declaration=yaml_data,
            yaml_path=yaml_path,
            default_lang=default_lang,
            fallback_lang=fallback_lang,
        )

    def generate_id(self) -> None:
        self.id = uuid4()

    def compile(self) -> None:
        """
        Compile the node. This method should be overridden in subclasses to implement specific compilation logic.
        """
        raise NotImplementedError("Subclasses must implement the compile method.")
