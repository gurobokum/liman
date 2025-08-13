from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ruamel.yaml import YAML

from liman_core.base.component import Component
from liman_core.errors import InvalidSpecError
from liman_core.plugins.auth.schemas import ServiceAccountSpec

if TYPE_CHECKING:
    from liman_core.registry import Registry

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class ServiceAccount(Component[ServiceAccountSpec]):
    """
    ServiceAccount provides authentication and authorization context for node execution
    """

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        registry: Registry,
        *,
        yaml_path: str | None = None,
        strict: bool = False,
        **kwargs: Any,
    ) -> Self:
        spec = ServiceAccountSpec(**data)
        return cls(
            spec,
            registry,
            initial_data=data,
            yaml_path=yaml_path,
            strict=strict,
        )

    @classmethod
    def from_yaml_path(
        cls,
        yaml_path: str | Path,
        registry: Registry,
        *,
        strict: bool = True,
        **kwargs: Any,
    ) -> Self:
        """
        Create a ServiceAccount from a YAML file.

        Args:
            yaml_path (str): Path to the YAML file.

        Returns:
            ServiceAccount: An instance of ServiceAccount initialized with the YAML data.
        """
        yaml = YAML()
        yaml_path_str = str(yaml_path)
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

    def get_internal_state(self, external_state: dict[str, Any]) -> dict[str, Any]:
        """
        Extract and return internal state from external state based on inject configuration
        """
        if not self.spec.context:
            return {}

        context_vars: dict[str, Any] = {}

        for var_spec in self.spec.context.inject:
            if ":" in var_spec:
                # Custom name assignment (e.g., "user_id: user.id")
                # would be accessed as self.context.user_id
                target_name, source_path = var_spec.split(":", 1)
                target_name = target_name.strip()
                source_path = source_path.strip()
            else:
                # Direct variable name (e.g., "organization.id")
                # would be accesed as self.context.organization.id
                target_name = var_spec
                source_path = var_spec

            # Navigate nested dictionary using dot notation
            value = self._get_nested_value(external_state, source_path)

            if value is None and self.spec.context.strict:
                raise ValueError(
                    f"Required context variable not found in state: '{source_path}'"
                )

            if value is not None:
                self._set_nested_value(context_vars, target_name, value)

        context_vars["__service_account__"] = self.name
        return context_vars

    def _get_nested_value(self, data: dict[str, Any], path: str) -> Any:
        keys = path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def _set_nested_value(self, data: dict[str, Any], path: str, value: Any) -> None:
        keys = path.split(".")
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value
