import pytest
from dishka import (
    AsyncContainer,
    Container,
    Provider,
    Scope,
    make_async_container,
    make_container,
    provide,
)

from liman_core import dishka as liman_dishka
from liman_core.registry import Registry


@pytest.fixture(scope="function")
def test_containers(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> tuple[Container, AsyncContainer]:
    """
    Setup test containers with fresh registry.

    Usage:
    - @pytest.mark.parametrize("test_containers", ["function"], indirect=True) - function scope
    - @pytest.mark.parametrize("test_containers", ["session"], indirect=True) - session scope
    - Default is function scope
    """
    scope = getattr(request, "param", "function")

    provider_scope = Scope.SESSION if scope == "session" else Scope.REQUEST

    class TestProvider(Provider):
        @provide(scope=provider_scope)
        def get_registry(self) -> Registry:
            return Registry()

    test_provider = TestProvider()
    test_container = make_container(test_provider)
    test_async_container = make_async_container(test_provider)

    monkeypatch.setattr(liman_dishka, "container", test_container)
    monkeypatch.setattr(liman_dishka, "async_container", test_async_container)

    return test_container, test_async_container
