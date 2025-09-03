from __future__ import annotations

import sys
from abc import ABC
from collections.abc import Sequence
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeAlias, TypeVar
from uuid import UUID, uuid4

from pydantic import Field, create_model
from rich import print as rich_print
from rich.syntax import Syntax
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import PreservedScalarString

from liman_core.base.schemas import S
from liman_core.errors import InvalidSpecError
from liman_core.plugins import PluginFieldConflictError

if TYPE_CHECKING:
    from liman_core.plugins.core.base import Plugin
    from liman_core.registry import Registry

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

ComponentT = TypeVar("ComponentT", bound="Component[Any]")


class Component(Generic[S], ABC):
    __slots__ = (
        "id",
        "name",
        "strict",
        # spec
        "spec",
        "yaml_path",
        "registry",
        # private
        "_initial_data",
    )

    spec: S
    spec_type: type[S]

    def __init__(
        self,
        spec: S,
        registry: Registry,
        *,
        initial_data: dict[str, Any] | None = None,
        yaml_path: str | None = None,
        strict: bool = True,
    ) -> None:
        self._initial_data = initial_data
        self.spec = spec
        self.yaml_path = yaml_path
        self.strict = strict
        self.registry = registry

        self.id = self.generate_id()
        self.name = self.spec.name

    def __repr__(self) -> str:
        return f"{self.spec.kind}:{self.name}"

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        registry: Registry,
        *,
        yaml_path: str | None = None,
        strict: bool = True,
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
        # Create extended spec with plugin fields
        plugins = registry.get_plugins(cls.__name__)
        ExtendedSpecClass = cls.create_extended_spec(cls.spec_type, plugins, data)

        spec = ExtendedSpecClass.model_validate(data, strict=strict)

        return cls(
            spec=spec,
            registry=registry,
            initial_data=data,
            yaml_path=yaml_path,
            strict=strict,
            **kwargs,
        )

    @classmethod
    def from_yaml_path(
        cls: type[ComponentT],
        yaml_path: str | Path,
        registry: Registry,
        *,
        strict: bool = True,
        **kwargs: Any,
    ) -> ComponentT:
        """
        Create a Component from a YAML file.

        Args:
            yaml_path (str | Path): Path to the YAML file.
            registry (Registry): Registry instance for plugins.

        Returns:
            Component: An instance of Component initialized with the YAML data.
        """
        yaml_path_str = str(yaml_path)
        yaml = YAML()
        with open(yaml_path_str, encoding="utf-8") as fd:
            yaml_data = yaml.load(fd)

        if not isinstance(yaml_data, dict):
            raise InvalidSpecError(
                "YAML content must be a dictionary at the top level."
            )

        return cls.from_dict(
            yaml_data,
            registry,
            yaml_path=yaml_path_str,
            strict=strict,
            **kwargs,
        )

    def generate_id(self) -> UUID:
        return uuid4()

    @classmethod
    def create_extended_spec(
        cls, base_spec_class: type[S], plugins: Sequence[Plugin], data: dict[str, Any]
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

            plugin_fields[plugin.field_name] = (plugin.field_type, Field(default=None))

        if plugin_fields:
            ExtendedSpecClass = create_model(
                f"{base_spec_class.__name__}WithPlugins",
                __base__=base_spec_class,
                **plugin_fields,
            )
            return ExtendedSpecClass

        return base_spec_class

    @property
    def full_name(self) -> str:
        """
        Get the full name of the component, which is a combination of its kind and name.
        """
        return f"{self.spec.kind}/{self.name}"

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
