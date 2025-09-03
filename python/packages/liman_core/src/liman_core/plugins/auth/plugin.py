from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeGuard

from liman_core.errors import ComponentNotFoundError, LimanError
from liman_core.plugins.auth.schemas import AuthFieldSpec
from liman_core.plugins.auth.service_account.component import ServiceAccount
from liman_core.plugins.auth.service_account.schemas import ServiceAccountSpec
from liman_core.plugins.core.base import Plugin

if TYPE_CHECKING:
    from liman_core.node_actor.actor import NodeActor, PreHookData
    from liman_core.registry import Registry


class AuthPlugin(Plugin):
    """
    AuthPlugin provides authentication and authorization context for node execution.
    """

    name = "AuthPlugin"
    applies_to = ["Node", "LLMNode", "ToolNode"]
    registered_kinds = ["ServiceAccount", "CredentialsProvider"]
    field_name = "auth"
    field_type = AuthFieldSpec

    def validate(self, spec_data: Any) -> Any: ...

    def apply(self, instance: Any) -> None:
        from liman_core.node_actor.actor import NodeActor

        if (
            isinstance(instance, NodeActor)
            and hasattr(instance.node.spec, "auth")
            and instance.node.spec.auth
        ):
            instance.add_pre_hook(self._inject_auth_context)

    def _inject_auth_context(
        self, actor: NodeActor[Any], data: PreHookData
    ) -> PreHookData:
        """
        Pre-execution hook: Inject authentication context into execution
        """
        if not hasattr(actor.node.spec, "auth") or not actor.node.spec.auth:
            return data

        registry = actor.node.registry
        auth_spec = actor.node.spec.auth

        service_account = self._resolve_service_account(
            auth_spec.service_account, registry
        )
        auth_context = service_account.get_internal_state(data["context"])

        data["context"].update(
            {
                "auth": {
                    "service_account": service_account.spec.name,
                    "context": auth_context,
                }
            }
        )

        return data

    def _resolve_service_account(
        self, sa_spec: str | ServiceAccountSpec, registry: Registry
    ) -> ServiceAccount:
        """
        Resolve service account from spec (string reference or inlined spec)
        """
        if isinstance(sa_spec, str):
            return registry.lookup(ServiceAccount, sa_spec)
        elif isinstance(sa_spec, ServiceAccountSpec):
            try:
                return registry.lookup(ServiceAccount, sa_spec.name)
            except ComponentNotFoundError:
                sa = ServiceAccount(sa_spec, registry=registry)
                registry.add(sa)
                return sa
        else:
            raise LimanError(f"Invalid service account spec: {sa_spec}")


class SpecWithAuth(Protocol):
    auth: AuthFieldSpec


def spec_has_auth(spec: Any) -> TypeGuard[SpecWithAuth]:
    return hasattr(spec, "auth") and spec.auth is not None
