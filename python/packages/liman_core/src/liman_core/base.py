import sys
from abc import ABC, abstractmethod
from io import StringIO
from typing import Any, Generic, TypeAlias, TypeVar
from uuid import UUID, uuid4

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


class BaseSpec(BaseModel):
    kind: str
    name: str


S = TypeVar("S", bound=BaseSpec)


class Output(BaseModel, Generic[S]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    response: BaseMessage

    next_nodes: list[tuple["BaseNode[S]", dict[str, Any]]] = []


class BaseNode(Generic[S], ABC):
    __slots__ = (
        "id",
        "name",
        "strict",
        # spec
        "spec",
        "yaml_path",
        # lang
        "default_lang",
        "fallback_lang",
        # private
        "_initial_data",
        "_compiled",
    )

    spec: S

    def __init__(
        self,
        spec: S,
        *,
        initial_data: dict[str, Any] | None = None,
        yaml_path: str | None = None,
        strict: bool = False,
        default_lang: str = "en",
        fallback_lang: str = "en",
    ) -> None:
        if not is_valid_language_code(default_lang):
            raise LimanError(f"Invalid default language code: {default_lang}")
        self.default_lang: LanguageCode = default_lang

        if not is_valid_language_code(fallback_lang):
            raise LimanError(f"Invalid fallback language code: {fallback_lang}")
        self.fallback_lang: LanguageCode = fallback_lang

        self._initial_data = initial_data
        self.spec = spec
        self.yaml_path = yaml_path

        self.id = self.generate_id()
        self.name = self.spec.name

        self.strict = strict
        self._compiled = False

    def __repr__(self) -> str:
        return f"{self.spec.kind}:{self.name}"

    @classmethod
    @abstractmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        yaml_path: str | None = None,
        strict: bool = False,
        default_lang: str = "en",
        fallback_lang: str = "en",
    ) -> Self:
        """
        Create a BaseNode instance from a dict spec

        Args:
            data (dict[str, Any]): Dictionary containing the BaseNode spec.
            yaml_path (str | None): Path to the YAML file if the data is loaded from a YAML file.
            strict (bool): Whether to enforce strict validation of the spec and other internal checks.
            default_lang (str): Default language for the node.
            fallback_lang (str): Fallback language for the node.

        Returns:
            BaseNode: An instance of initialized BaseMNode
        """
        ...

    @classmethod
    def from_yaml_path(
        cls,
        yaml_path: str,
        *,
        strict: bool = True,
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
        yaml = YAML()
        with open(yaml_path, encoding="utf-8") as fd:
            yaml_data = yaml.load(fd)

        return cls.from_dict(
            yaml_data,
            yaml_path=yaml_path,
            strict=strict,
            default_lang=default_lang,
            fallback_lang=fallback_lang,
        )

    def generate_id(self) -> UUID:
        return uuid4()

    @abstractmethod
    def compile(self) -> None:
        """
        Compile the node. This method should be overridden in subclasses to implement specific compilation logic.
        """
        ...

    @abstractmethod
    def invoke(self, *args: Any, **kwargs: Any) -> Output[Any]: ...

    @abstractmethod
    async def ainvoke(self, *args: Any, **kwargs: Any) -> Output[Any]: ...

    @property
    def is_llm_node(self) -> bool:
        return self.spec.kind == "LLMNode"

    @property
    def is_tool_node(self) -> bool:
        return self.spec.kind == "ToolNode"

    def print_spec(self, initial: bool = False) -> None:
        """
        Print the tool node specification in YAML format.
        Args:
            raw (bool): If True, print the raw declaration; otherwise, print the validated spec.
        """
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.preserve_quotes = True

        yaml_spec = StringIO()

        if initial:
            to_dump = _preserve_multiline_strings(self._initial_data)
        else:
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
