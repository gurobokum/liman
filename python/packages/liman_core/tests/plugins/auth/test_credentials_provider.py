import pytest

from liman_core.errors import InvalidSpecError
from liman_core.plugins.auth.credentials_provider.component import CredentialsProvider
from liman_core.registry import Registry


def mock_function() -> dict[str, str]:
    return {"token": "mock_token", "type": "bearer"}


VALID_CREDENTIALS_PROVIDER_BEARER = {
    "kind": "CredentialsProvider",
    "name": "BearerProvider",
    "type": "bearer",
    "func": "tests.plugins.auth.test_credentials_provider.mock_function",
}

VALID_CREDENTIALS_PROVIDER_AWS = {
    "kind": "CredentialsProvider",
    "name": "AWSProvider",
    "type": "aws",
    "func": "tests.plugins.auth.test_credentials_provider.mock_function",
}

INVALID_CREDENTIALS_PROVIDER_MISSING_FUNC = {
    "kind": "CredentialsProvider",
    "name": "InvalidProvider",
    "type": "bearer",
}

INVALID_CREDENTIALS_PROVIDER_NONEXISTENT_FUNC = {
    "kind": "CredentialsProvider",
    "name": "NonexistentProvider",
    "type": "bearer",
    "func": "nonexistent.module.function",
}


def test_credentials_provider_creation_bearer(registry: Registry) -> None:
    provider = CredentialsProvider.from_dict(
        VALID_CREDENTIALS_PROVIDER_BEARER, registry
    )

    assert provider.spec.name == "BearerProvider"
    assert provider.spec.type_ == "bearer"
    assert provider.func is not None
    assert callable(provider.func)
    result = provider.func()
    print(provider.func)
    assert result == {"token": "mock_token", "type": "bearer"}


def test_credentials_provider_creation_aws(registry: Registry) -> None:
    provider = CredentialsProvider.from_dict(VALID_CREDENTIALS_PROVIDER_AWS, registry)

    assert provider.spec.name == "AWSProvider"
    assert provider.spec.type_ == "aws"
    assert provider.func is not None
    assert callable(provider.func)


def test_credentials_provider_all_types(registry: Registry) -> None:
    types = ["bearer", "basic", "aws", "gcp", "azure", "custom"]

    for provider_type in types:
        config = {
            "kind": "CredentialsProvider",
            "name": f"{provider_type.upper()}Provider",
            "type": provider_type,
            "func": "tests.plugins.auth.test_credentials_provider.mock_function",
        }

        provider = CredentialsProvider.from_dict(config, registry)
        assert provider.spec.type_ == provider_type
        assert provider.func is not None


def test_credentials_provider_invalid_function_strict(registry: Registry) -> None:
    with pytest.raises(InvalidSpecError, match="Failed to import module for function"):
        CredentialsProvider.from_dict(
            INVALID_CREDENTIALS_PROVIDER_NONEXISTENT_FUNC, registry
        )


def test_credentials_provider_invalid_function_non_strict(registry: Registry) -> None:
    provider = CredentialsProvider.from_dict(
        INVALID_CREDENTIALS_PROVIDER_NONEXISTENT_FUNC, registry, strict=False
    )

    assert provider.func is not None
    assert callable(provider.func)
    assert provider.func() is None


def test_credentials_provider_non_callable_attribute_strict(registry: Registry) -> None:
    config = {
        "kind": "CredentialsProvider",
        "name": "NonCallableProvider",
        "type": "bearer",
        "func": "packages.liman_core.tests.plugins.auth.credentials_provider.test_component.__name__",
    }

    with pytest.raises(InvalidSpecError, match="Failed to import module for function"):
        CredentialsProvider.from_dict(config, registry, strict=True)


def test_credentials_provider_non_callable_attribute_non_strict(
    registry: Registry,
) -> None:
    config = {
        "kind": "CredentialsProvider",
        "name": "NonCallableProvider",
        "type": "bearer",
        "func": "packages.liman_core.tests.plugins.auth.credentials_provider.test_component.__name__",
    }

    provider = CredentialsProvider.from_dict(config, registry, strict=False)

    assert provider.func is not None
    assert callable(provider.func)
    assert provider.func() is None


def test_credentials_provider_full_name(registry: Registry) -> None:
    provider = CredentialsProvider.from_dict(
        VALID_CREDENTIALS_PROVIDER_BEARER, registry
    )

    assert provider.full_name == "CredentialsProvider/BearerProvider"


def test_credentials_provider_repr(registry: Registry) -> None:
    provider = CredentialsProvider.from_dict(
        VALID_CREDENTIALS_PROVIDER_BEARER, registry
    )

    assert repr(provider) == "CredentialsProvider:BearerProvider"
