import sys
from abc import ABC, abstractmethod
from io import StringIO
from typing import Any, Generic, TypeAlias, TypeVar
from uuid import uuid4

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, ConfigDict
from rich import print as rich_print
from rich.syntax import Syntax
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import PreservedScalarString

from liman_core.errors import LimanError
from liman_core.languages import LanguageCode, is_valid_language_code

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

S = TypeVar("S", bound=BaseModel)


class Output(Generic[S], BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    response: BaseMessage

    next_nodes: list[tuple["BaseNode[S]", dict[str, Any]]] = []


class BaseNode(Generic[S], ABC):
    __slots__ = (
        "id",
        "name",
        "declaration",
        "spec",
        "yaml_path",
        "default_lang",
        "fallback_lang",
        "kind",
        "_compiled",
    )

    spec: S

    def __init__(
        self,
        name: str,
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

        self.kind = "BaseNode"
        self.name = name

        self.generate_id()
        self._compiled = False

    @classmethod
    def from_yaml(
        cls,
        yaml_data: dict[str, Any],
        *,
        default_lang: str = "en",
        fallback_lang: str = "en",
    ) -> Self:
        """
        Create a BaseNode instance from a YAML dictionary.

        Args:
            yaml_data (dict[str, Any]): Dictionary containing YAML data.

        Returns:
            BaseNode: An instance of BaseNode initialized with the YAML data.
        """
        name = yaml_data.get("name")
        if not name:
            raise LimanError("YAML data must contain a 'name' field.")
        return cls(
            name=name,
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
    ) -> Self:
        """
        Create a BaseNode instance from a YAML file.

        Args:
            yaml_path (str): Path to the YAML file.

        Returns:
            BaseNode: An instance of BaseNode initialized with the YAML data.
        """
        yaml_data = YAML().load(yaml_path).dict()
        name = yaml_data.get("name")
        if not name:
            raise LimanError("YAML data must contain a 'name' field.")
        return cls(
            name,
            declaration=yaml_data,
            yaml_path=yaml_path,
            default_lang=default_lang,
            fallback_lang=fallback_lang,
        )

    def generate_id(self) -> None:
        self.id = uuid4()

    @abstractmethod
    def compile(self) -> None:
        """
        Compile the node. This method should be overridden in subclasses to implement specific compilation logic.
        """
        ...

    @property
    def is_llm_node(self) -> bool:
        return self.kind == "LLMNode"

    @property
    def is_tool_node(self) -> bool:
        return self.kind == "ToolNode"

    def print_spec(self, raw: bool = False) -> None:
        """
        Print the tool node specification in YAML format.
        Args:
            raw (bool): If True, print the raw declaration; otherwise, print the validated spec.
        """
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.preserve_quotes = True

        yaml_spec = StringIO()

        if raw:
            to_dump = _preserve_multiline_strings(self.declaration)
        else:
            if not self.spec or not isinstance(self.spec, BaseModel):
                raise LimanError("Node specification is not compiled yet.")
            to_dump = _preserve_multiline_strings(
                self.spec.model_dump(exclude_none=True)
            )

        yaml.dump(to_dump, yaml_spec)

        syntax = Syntax(
            yaml_spec.getvalue(),
            "yaml",
            theme="monokai",
            background_color="default",
            word_wrap=True,
        )
        rich_print(syntax)


YamlValue: TypeAlias = dict[str, Any] | list["YamlValue"] | str


def _preserve_multiline_strings(data: YamlValue | None) -> YamlValue | None:
    """
    Recursively convert multiline strings to PreservedScalarString
    so that YAML dumps them as block scalars (|).
    """
    if data is None:
        return None

    if isinstance(data, str) and "\n" in data:
        return PreservedScalarString(data)
    elif isinstance(data, dict):
        return {k: _preserve_multiline_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [v for i in data if (v := _preserve_multiline_strings(i)) is not None]
    return data
