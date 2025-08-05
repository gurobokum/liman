from typing import Any

from liman_core.auth.schemas import ServiceAccountSpec
from liman_core.base.component import Component


class ServiceAccount(Component[ServiceAccountSpec]):
    """
    ServiceAccount provides authentication and authorization context for node execution
    """

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        yaml_path: str | None = None,
        strict: bool = False,
        **kwargs: Any,
    ) -> "ServiceAccount":
        spec = ServiceAccountSpec(**data)
        return cls(
            spec=spec,
            initial_data=data,
            yaml_path=yaml_path,
            strict=strict,
        )

    def get_context_variables(self, external_state: dict[str, Any]) -> dict[str, Any]:
        """
        Extract and return context variables from external state based on inject configuration
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
