import pytest

from liman_core.registry import Registry


@pytest.fixture
def registry() -> Registry:
    return Registry()
