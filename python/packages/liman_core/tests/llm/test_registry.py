import logging

import pytest

from liman_core.errors import LimanError
from liman_core.llm.registry import load_models_registry, resolve_model
from liman_core.llm.schemas import ModelsRegistry


def test_load_models_registry_parses_bundled_yaml() -> None:
    registry = load_models_registry()

    assert set(registry.providers) >= {
        "openai",
        "google",
        "anthropic",
        "deepseek",
        "ollama",
    }
    for provider in registry.providers.values():
        assert provider.module
        assert provider.cls
        assert provider.package
        for model in provider.models.values():
            if model.pricing:
                assert model.pricing.input >= 0
                assert model.pricing.output >= 0


def test_resolve_model_canonical() -> None:
    info = resolve_model("openai/gpt-4o")

    assert info.provider == "openai"
    assert info.name == "gpt-4o"
    assert info.pricing is not None
    assert info.pricing.input == 2.5


def test_resolve_model_alias_warns(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        info = resolve_model("gpt-4o")

    assert info.provider == "openai"
    assert "openai/gpt-4o" in caplog.text


def test_resolve_model_is_case_insensitive() -> None:
    info = resolve_model("OpenAI/GPT-4o")

    assert info.provider == "openai"
    assert info.name == "gpt-4o"
    assert info.pricing is not None


def test_resolve_model_canonical_unknown_model_allowed() -> None:
    info = resolve_model("openai/my-finetune")

    assert info.provider == "openai"
    assert info.name == "my-finetune"
    assert info.pricing is None


def test_resolve_model_unknown_provider() -> None:
    with pytest.raises(LimanError, match="Unknown LLM provider"):
        resolve_model("replicate/some-model")


def test_resolve_model_unknown_alias() -> None:
    with pytest.raises(LimanError, match="LangChain chat model instance"):
        resolve_model("mystery-model")


def test_resolve_model_ambiguous_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = ModelsRegistry.model_validate(
        {
            "providers": {
                "one": {
                    "package": "pkg-one",
                    "module": "mod_one",
                    "class": "ChatOne",
                    "models": {"shared": {}},
                },
                "two": {
                    "package": "pkg-two",
                    "module": "mod_two",
                    "class": "ChatTwo",
                    "models": {"shared": {}},
                },
            }
        }
    )
    monkeypatch.setattr(
        "liman_core.llm.registry.load_models_registry", lambda: registry
    )

    with pytest.raises(LimanError, match="Ambiguous model alias"):
        resolve_model("shared")
