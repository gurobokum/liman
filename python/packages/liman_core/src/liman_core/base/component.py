import sys
from abc import ABC, abstractmethod
from io import StringIO
from typing import Any, Generic, TypeAlias
from uuid import UUID, uuid4

from pydantic import create_model
from rich import print as rich_print
from rich.syntax import Syntax
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import PreservedScalarString

from liman_core.base.schemas import S
from liman_core.errors import InvalidSpecError
from liman_core.plugins import PluginFieldConflictError
from liman_core.plugins.core.base import Plugin

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class Component(Generic[S], ABC):
    __slots__ = (
        "id",
        "name",
        "strict",
        # spec
        "spec",
        "yaml_path",
        # private
        "_initial_data",
    )

    spec: S

    def __init__(
        self,
        spec: S,
        *,
        initial_data: dict[str, Any] | None = None,
        yaml_path: str | None = None,
        strict: bool = False,
    ) -> None:
        self._initial_data = initial_data
        self.spec = spec
        self.yaml_path = yaml_path
        self.strict = strict

        self.id = self.generate_id()
        self.name = self.spec.name

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
        **kwargs: Any,
    ) -> Self:
        """
        Create a Component from a dict spec

        Args:
            data (dict[str, Any]): Dictionary containing the BaseNode spec.
            yaml_path (str | None): Path to the YAML file if the data is loaded from a YAML file.
            strict (bool): Whether to enforce strict validation of the spec and other internal checks.
            **kwargs: Additional keyword arguments specific to the subclass.

        Returns:
            Component: An instance of initialized Component
        """
        ...

    @classmethod
    def from_yaml_path(
        cls,
        yaml_path: str,
        *,
        strict: bool = True,
        **kwargs: Any,
    ) -> Self:
        """
        Create a Component from a YAML file.

        Args:
            yaml_path (str): Path to the YAML file.

        Returns:
            Component: An instance of Component initialized with the YAML data.
        """
        yaml = YAML()
        with open(yaml_path, encoding="utf-8") as fd:
            yaml_data = yaml.load(fd)

        if not isinstance(yaml_data, dict):
            raise InvalidSpecError(
                "YAML content must be a dictionary at the top level."
            )

        return cls.from_dict(
            yaml_data,
            yaml_path=yaml_path,
            strict=strict,
            **kwargs,
        )

    def generate_id(self) -> UUID:
        return uuid4()

    @classmethod
    def create_extended_spec(
        cls, base_spec_class: type[S], plugins: list[Plugin], data: dict[str, Any]
    ) -> type[S]:
        """
        Create extended spec class with plugin fields and validate data.

        Returns:
            Tuple of (ExtendedSpecClass, validated_data)
        """
        if not plugins:
            return base_spec_class

        kind = data.get("kind")
        if not kind:
            raise InvalidSpecError("Spec data must contain 'kind' field")

        plugin_fields: dict[str, Any] = {}
        for plugin in plugins:
            if kind not in plugin.applies_to:
                continue

            if hasattr(base_spec_class, plugin.field_name):
                raise PluginFieldConflictError(
                    f"Field '{plugin.field_name}' already exists in {kind} spec"
                )

            plugin_fields[plugin.field_name] = (plugin.field_type, ...)

        if plugin_fields:
            ExtendedSpecClass = create_model(
                f"{base_spec_class.__name__}WithPlugins",
                __base__=base_spec_class,
                **plugin_fields,
            )
            return ExtendedSpecClass

        return base_spec_class

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
