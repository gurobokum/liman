import asyncio

from liman_core.nodes.tool_node.node import ToolNode
from liman_core.plugins.auth.credentials_provider.component import CredentialsProvider
from liman_core.plugins.auth.plugin import spec_has_auth
from liman_core.plugins.auth.service_account.component import ServiceAccount
from liman_core.plugins.auth.service_account.schemas import ServiceAccountSpec
from liman_core.registry import Registry


def mock_user_credentials() -> dict[str, str]:
    return {"token": "user_access_token", "type": "bearer"}


async def async_mock_admin_credentials() -> dict[str, str]:
    return {"token": "admin_access_token", "type": "bearer"}


TOOL_NODE_WITH_INLINED_AUTH = {
    "kind": "ToolNode",
    "name": "UserLookupTool",
    "description": "Look up user information",
    "auth": {
        "service_account": {
            "context": {"inject": ["user_id"]},
            "credentials_provider": "UserDataCredentials",
        }
    },
    "func": "test.lookup_user",
}

USER_DATA_CREDENTIALS_PROVIDER = {
    "kind": "CredentialsProvider",
    "name": "UserDataCredentials",
    "type": "bearer",
    "func": (
        "tests.plugins.auth.test_credentials_provider_integration.mock_user_credentials"
    ),
}

ADMIN_CREDENTIALS_PROVIDER = {
    "kind": "CredentialsProvider",
    "name": "AdminCredentials",
    "type": "custom",
    "func": (
        "tests.plugins.auth.test_credentials_provider_integration."
        "async_mock_admin_credentials"
    ),
}

COMPLEX_TOOL_NODE = {
    "kind": "ToolNode",
    "name": "AdminTool",
    "description": "Administrative operations",
    "auth": {
        "service_account": {
            "context": {"inject": ["admin_id", "organization_id"]},
            "credentials_providers": ["UserDataCredentials", "AdminCredentials"],
        }
    },
    "func": "test.admin_operation",
}


def test_inlined_service_account_creation(registry: Registry) -> None:
    credentials_provider = CredentialsProvider.from_dict(
        USER_DATA_CREDENTIALS_PROVIDER, registry
    )
    registry.add(credentials_provider)

    node = ToolNode.from_dict(TOOL_NODE_WITH_INLINED_AUTH, registry)

    assert spec_has_auth(node.spec)
    service_account_spec = node.spec.auth.service_account

    assert service_account_spec is not None
    assert isinstance(service_account_spec, ServiceAccountSpec)
    assert service_account_spec.context is not None
    assert "user_id" in service_account_spec.context.inject
    assert service_account_spec.credentials_provider == "UserDataCredentials"


def test_credentials_provider_registration_and_lookup(registry: Registry) -> None:
    credentials_provider = CredentialsProvider.from_dict(
        USER_DATA_CREDENTIALS_PROVIDER, registry
    )
    registry.add(credentials_provider)

    retrieved = registry.lookup(CredentialsProvider, "UserDataCredentials")
    assert retrieved.spec.name == "UserDataCredentials"
    assert retrieved.spec.type_ == "bearer"

    credentials = asyncio.run(retrieved.invoke())
    assert credentials == {"token": "user_access_token", "type": "bearer"}


def test_service_account_with_credentials_provider_access(registry: Registry) -> None:
    credentials_provider = CredentialsProvider.from_dict(
        USER_DATA_CREDENTIALS_PROVIDER, registry
    )
    registry.add(credentials_provider)

    service_account = ServiceAccount.from_dict(
        {
            "kind": "ServiceAccount",
            "name": "TestServiceAccount",
            "context": {"inject": ["user_id"]},
            "credentials_provider": "UserDataCredentials",
        },
        registry,
    )

    internal_state = service_account.get_internal_state({"user_id": "test_user_123"})

    assert internal_state["user_id"] == "test_user_123"

    provider = registry.lookup(CredentialsProvider, "UserDataCredentials")
    credentials = asyncio.run(provider.invoke())
    assert credentials["token"] == "user_access_token"


def test_multiple_credentials_providers(registry: Registry) -> None:
    user_provider = CredentialsProvider.from_dict(
        USER_DATA_CREDENTIALS_PROVIDER, registry
    )
    admin_provider = CredentialsProvider.from_dict(ADMIN_CREDENTIALS_PROVIDER, registry)

    registry.add(user_provider)
    registry.add(admin_provider)

    node = ToolNode.from_dict(COMPLEX_TOOL_NODE, registry)

    assert spec_has_auth(node.spec)
    service_account_spec = node.spec.auth.service_account
    assert isinstance(service_account_spec, ServiceAccountSpec)
    assert service_account_spec.credentials_providers == [
        "UserDataCredentials",
        "AdminCredentials",
    ]

    user_creds = registry.lookup(CredentialsProvider, "UserDataCredentials")
    admin_creds = registry.lookup(CredentialsProvider, "AdminCredentials")

    assert asyncio.run(user_creds.invoke()) == {
        "token": "user_access_token",
        "type": "bearer",
    }
    assert asyncio.run(admin_creds.invoke()) == {
        "token": "admin_access_token",
        "type": "bearer",
    }


def test_auth_integration_full_flow(registry: Registry) -> None:
    credentials_provider = CredentialsProvider.from_dict(
        USER_DATA_CREDENTIALS_PROVIDER, registry
    )
    registry.add(credentials_provider)

    node = ToolNode.from_dict(TOOL_NODE_WITH_INLINED_AUTH, registry)
    node_name = node.spec.name

    assert spec_has_auth(node.spec)
    auth_sa = node.spec.auth.service_account
    assert isinstance(auth_sa, ServiceAccountSpec)
    assert auth_sa.context is not None

    service_account = ServiceAccount.from_dict(
        {
            "kind": "ServiceAccount",
            "name": "InlinedServiceAccount",
            "context": auth_sa.context.model_dump(),
            "credentials_provider": auth_sa.credentials_provider,
        },
        registry,
    )
    internal_state = service_account.get_internal_state({"user_id": "user_456"})

    assert internal_state["user_id"] == "user_456"

    assert service_account.spec.credentials_provider is not None
    provider = registry.lookup(
        CredentialsProvider, service_account.spec.credentials_provider
    )
    credentials = asyncio.run(provider.invoke())

    assert credentials["token"] == "user_access_token"
    assert credentials["type"] == "bearer"
    assert node_name == "UserLookupTool"
    assert auth_sa.credentials_provider == "UserDataCredentials"
