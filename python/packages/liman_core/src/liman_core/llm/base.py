import os
from importlib import import_module
from typing import Any, cast

from langchain_core.language_models.chat_models import BaseChatModel

from liman_core.errors import LimanError
from liman_core.llm.registry import load_models_registry, resolve_model


def get_llm(ref: str, *, api_key: str | None = None, **kwargs: Any) -> BaseChatModel:
    """
    Build a LangChain chat model from a model ref.

    Canonical ref is 'provider/model' ("openai/gpt-4o"); bare model names
    work as aliases with a warning. The provider package is imported lazily.
    The api key is taken from the argument or the provider env var.
    """
    info = resolve_model(ref)
    provider = load_models_registry().providers[info.provider]

    try:
        module = import_module(provider.module)
    except ImportError as e:
        raise LimanError(
            f"Provider package is not installed for '{ref}': "
            f"uv add {provider.package} (or pip install {provider.package})"
        ) from e

    llm_cls = cast(type[BaseChatModel], getattr(module, provider.cls))

    if provider.env_key:
        api_key = api_key or os.environ.get(provider.env_key)
        if not api_key:
            raise LimanError(
                f"Api key is missing for '{ref}': set {provider.env_key} or pass api_key"
            )
        return llm_cls(model=info.name, api_key=api_key, **kwargs)
    return llm_cls(model=info.name, **kwargs)
