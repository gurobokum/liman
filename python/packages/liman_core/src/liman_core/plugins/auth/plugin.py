from __future__ import annotations

from typing import TYPE_CHECKING, Any

from liman_core.base.component import Component
from liman_core.errors import ComponentNotFoundError, LimanError
from liman_core.plugins.auth.schemas import AuthFieldSpec, ServiceAccountSpec
from liman_core.plugins.auth.service_account import ServiceAccount
from liman_core.plugins.core.base import ExecutionStateProvider, Plugin

if TYPE_CHECKING:
    from liman_core.registry import Registry


class AuthPlugin(Plugin, ExecutionStateProvider):
    """
    AuthPlugin provides authentication and authorization context for node execution.
    """

    name = "AuthPlugin"
    applies_to = ["Node", "LLMNode", "ToolNode"]
    registered_kinds = ["ServiceAccount"]
    field_name = "auth"
    field_type = AuthFieldSpec

    def validate(self, spec_data: Any) -> Any: ...

    def get_execution_state(
        self, component: Component[Any], state: dict[str, Any], registry: Registry
    ) -> dict[str, Any]:
        if component.spec.kind not in self.applies_to:
            raise LimanError(
                f"AuthPlugin cannot provide execution state for component of kind '{component.spec.kind}'"
            )

        auth = getattr(component.spec, self.field_name, None)
        if not auth:
            return state

        sa_spec = auth.service_account
        if isinstance(sa_spec, str):
            sa = registry.lookup(ServiceAccount, sa_spec)
        elif isinstance(sa_spec, ServiceAccountSpec):
            try:
                sa = registry.lookup(ServiceAccount, sa_spec.name)
            except ComponentNotFoundError:
                sa = ServiceAccount(sa_spec, registry=registry)
                registry.add(sa)
        else:
            return {}

        return sa.get_internal_state(state)
