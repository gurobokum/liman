import sys
from types import ModuleType
from typing import Any

import pytest

from liman_core.errors import LimanError
from liman_core.llm.base import get_llm
from liman_core.llm.schemas import ModelsRegistry

CAPTURED: list[dict[str, Any]] = []


class FakeChat:
    def __init__(self, **kwargs: Any) -> None:
        CAPTURED.append(kwargs)


@pytest.fixture
def fake_registry(monkeypatch: pytest.MonkeyPatch) -> ModelsRegistry:
    registry = ModelsRegistry.model_validate(
        {
            "providers": {
                "fakeprov": {
                    "package": "langchain-fakeprov",
                    "module": "fake_llm_mod",
                    "class": "FakeChat",
                    "env_key": "FAKE_API_KEY",
                    "models": {"fake-model": {}},
                },
                "keyless": {
                    "package": "langchain-keyless",
                    "module": "fake_keyless_mod",
                    "class": "FakeChat",
                    "models": {"local-model": {}},
                },
                "missing": {
                    "package": "langchain-missing",
                    "module": "definitely_missing_module_xyz",
                    "class": "FakeChat",
                    "models": {"ghost-model": {}},
                },
            }
        }
    )
    monkeypatch.setattr(
        "liman_core.llm.registry.load_models_registry", lambda: registry
    )
    monkeypatch.setattr("liman_core.llm.base.load_models_registry", lambda: registry)

    fake_module = ModuleType("fake_llm_mod")
    fake_module.FakeChat = FakeChat  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "fake_llm_mod", fake_module)

    keyless_module = ModuleType("fake_keyless_mod")
    keyless_module.FakeChat = FakeChat  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "fake_keyless_mod", keyless_module)

    CAPTURED.clear()
    return registry


def test_get_llm_with_env_key(
    fake_registry: ModelsRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_API_KEY", "env-secret")

    get_llm("fakeprov/fake-model", temperature=0)

    assert CAPTURED == [
        {"model": "fake-model", "api_key": "env-secret", "temperature": 0}
    ]


def test_get_llm_explicit_key_wins(
    fake_registry: ModelsRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_API_KEY", "env-secret")

    get_llm("fakeprov/fake-model", api_key="explicit")

    assert CAPTURED == [{"model": "fake-model", "api_key": "explicit"}]


def test_get_llm_missing_key(
    fake_registry: ModelsRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("FAKE_API_KEY", raising=False)

    with pytest.raises(LimanError, match="FAKE_API_KEY"):
        get_llm("fakeprov/fake-model")


def test_get_llm_keyless_provider(fake_registry: ModelsRegistry) -> None:
    get_llm("keyless/local-model")

    assert CAPTURED == [{"model": "local-model"}]


def test_get_llm_missing_package(fake_registry: ModelsRegistry) -> None:
    with pytest.raises(LimanError, match="uv add langchain-missing"):
        get_llm("missing/ghost-model")
