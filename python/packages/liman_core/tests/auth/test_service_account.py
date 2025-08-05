import pytest

from liman_core.auth import ServiceAccount
from liman_core.errors import InvalidSpecError

VALID_SERVICE_ACCOUNT_WITH_CONTEXT = {
    "kind": "ServiceAccount",
    "name": "TestServiceAccount",
    "context": {"strict": True, "inject": ["user_id: user.id", "organization.id"]},
}

VALID_SERVICE_ACCOUNT_WITH_CREDENTIALS_PROVIDER = {
    "kind": "ServiceAccount",
    "name": "TestServiceAccount",
    "credentials_provider": "AWSCredentials",
}

VALID_SERVICE_ACCOUNT_WITH_CREDENTIALS_PROVIDERS = {
    "kind": "ServiceAccount",
    "name": "TestServiceAccount",
    "credentials_providers": ["AWSCredentials", "GCPCredentials"],
}

VALID_SERVICE_ACCOUNT_WITH_BOTH_CONTEXT_AND_CREDENTIALS = {
    "kind": "ServiceAccount",
    "name": "TestServiceAccount",
    "context": {"strict": False, "inject": ["project_id"]},
    "credentials_provider": "GCPCredentials",
}

INVALID_SERVICE_ACCOUNT_EMPTY = {"kind": "ServiceAccount", "name": "TestServiceAccount"}

INVALID_SERVICE_ACCOUNT_BOTH_CREDENTIALS = {
    "kind": "ServiceAccount",
    "name": "TestServiceAccount",
    "credentials_provider": "AWSCredentials",
    "credentials_providers": ["GCPCredentials"],
}

INVALID_SERVICE_ACCOUNT_EMPTY_INJECT = {
    "kind": "ServiceAccount",
    "name": "TestServiceAccount",
    "context": {"strict": True, "inject": []},
}


def test_service_account_with_context() -> None:
    service_account = ServiceAccount.from_dict(VALID_SERVICE_ACCOUNT_WITH_CONTEXT)
    assert service_account.spec.name == "TestServiceAccount"
    assert service_account.spec.context is not None
    assert service_account.spec.context.strict is True
    assert len(service_account.spec.context.inject) == 2


def test_service_account_with_single_credentials_provider() -> None:
    service_account = ServiceAccount.from_dict(
        VALID_SERVICE_ACCOUNT_WITH_CREDENTIALS_PROVIDER
    )
    assert service_account.spec.name == "TestServiceAccount"
    assert service_account.spec.credentials_provider == "AWSCredentials"
    assert service_account.spec.credentials_providers is None


def test_service_account_with_multiple_credentials_providers() -> None:
    service_account = ServiceAccount.from_dict(
        VALID_SERVICE_ACCOUNT_WITH_CREDENTIALS_PROVIDERS
    )
    assert service_account.spec.name == "TestServiceAccount"
    assert service_account.spec.credentials_providers == [
        "AWSCredentials",
        "GCPCredentials",
    ]
    assert service_account.spec.credentials_provider is None


def test_service_account_with_context_and_credentials() -> None:
    service_account = ServiceAccount.from_dict(
        VALID_SERVICE_ACCOUNT_WITH_BOTH_CONTEXT_AND_CREDENTIALS
    )
    assert service_account.spec.name == "TestServiceAccount"
    assert service_account.spec.context is not None
    assert service_account.spec.credentials_provider == "GCPCredentials"


def test_service_account_empty_raises_error() -> None:
    with pytest.raises(
        InvalidSpecError,
        match="ServiceAccount must have either credentials_provider/credentials_providers or context",
    ):
        ServiceAccount.from_dict(INVALID_SERVICE_ACCOUNT_EMPTY)


def test_service_account_both_credentials_raises_error() -> None:
    with pytest.raises(
        InvalidSpecError,
        match="Cannot specify both credentials_provider and credentials_providers",
    ):
        ServiceAccount.from_dict(INVALID_SERVICE_ACCOUNT_BOTH_CREDENTIALS)


def test_service_account_empty_inject_raises_error() -> None:
    with pytest.raises(InvalidSpecError, match="inject list cannot be empty"):
        ServiceAccount.from_dict(INVALID_SERVICE_ACCOUNT_EMPTY_INJECT)


def test_context_variables_extraction() -> None:
    external_state = {
        "user": {"id": "user123"},
        "organization": {"id": "org456"},
        "project": {"id": "proj789"},
    }

    service_account = ServiceAccount.from_dict(VALID_SERVICE_ACCOUNT_WITH_CONTEXT)
    context = service_account.get_context_variables(external_state)

    assert context["user_id"] == "user123"
    assert context["organization"]["id"] == "org456"


def test_context_variables_missing_strict_mode() -> None:
    external_state = {"user": {"id": "user123"}}

    service_account = ServiceAccount.from_dict(VALID_SERVICE_ACCOUNT_WITH_CONTEXT)

    with pytest.raises(
        ValueError,
        match="Required context variable not found in state: 'organization.id'",
    ):
        service_account.get_context_variables(external_state)


def test_context_variables_missing_non_strict_mode() -> None:
    external_state = {"user": {"id": "user123"}}

    non_strict_config = {
        "kind": "ServiceAccount",
        "name": "TestServiceAccount",
        "context": {"strict": False, "inject": ["user_id: user.id", "organization.id"]},
    }

    service_account = ServiceAccount.from_dict(non_strict_config)
    context = service_account.get_context_variables(external_state)

    assert context["user_id"] == "user123"
    assert "organization" not in context


def test_context_variables_nested_paths() -> None:
    external_state = {"user": {"profile": {"personal": {"email": "test@example.com"}}}}

    config = {
        "kind": "ServiceAccount",
        "name": "TestServiceAccount",
        "context": {"strict": True, "inject": ["email: user.profile.personal.email"]},
    }

    service_account = ServiceAccount.from_dict(config)
    context = service_account.get_context_variables(external_state)

    assert context["email"] == "test@example.com"


def test_context_variables_no_external_state() -> None:
    service_account = ServiceAccount.from_dict(VALID_SERVICE_ACCOUNT_WITH_CONTEXT)
    with pytest.raises(
        ValueError,
        match="Required context variable not found in state: 'user.id'",
    ):
        service_account.get_context_variables({})


def test_service_account_without_context() -> None:
    service_account = ServiceAccount.from_dict(
        VALID_SERVICE_ACCOUNT_WITH_CREDENTIALS_PROVIDER
    )
    context = service_account.get_context_variables({"some": "state"})
    assert context == {}


def test_get_context_variables_method() -> None:
    external_state = {
        "user": {"id": "user123", "name": "John"},
        "organization": {"id": "org456", "name": "TestOrg"},
    }

    service_account = ServiceAccount.from_dict(VALID_SERVICE_ACCOUNT_WITH_CONTEXT)
    context = service_account.get_context_variables(external_state)

    assert context["user_id"] == "user123"
    assert context["organization"]["id"] == "org456"
    assert "name" not in context["organization"]
