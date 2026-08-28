import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from ruamel.yaml import YAML

from liman_core.errors import LimanError
from liman_core.llm.schemas import ModelsRegistry, Pricing

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_models_registry() -> ModelsRegistry:
    """
    Load and validate the bundled models.yaml.
    """
    path = Path(__file__).parent / "models.yaml"
    with open(path, encoding="utf-8") as fd:
        data = YAML(typ="safe").load(fd)
    return ModelsRegistry.model_validate(data)


@dataclass(frozen=True)
class ModelInfo:
    provider: str
    name: str
    pricing: Pricing | None


def resolve_model(ref: str) -> ModelInfo:
    """
    Resolve a model ref to (provider, name, pricing).

    'provider/model' is the canonical form. A bare model name is an alias:
    it resolves by exact match across providers and logs a warning to use
    the canonical name. An alias found under several providers raises.
    """
    ref = ref.lower()
    registry = load_models_registry()

    if "/" in ref:
        provider, _, name = ref.partition("/")
        if provider not in registry.providers:
            raise LimanError(
                f"Unknown LLM provider '{provider}', supported: {sorted(registry.providers)}. "
                "For other providers pass any LangChain chat model instance as llm directly"
            )
        model = registry.providers[provider].models.get(name)
        return ModelInfo(provider, name, model.pricing if model else None)

    matches = [
        provider for provider, pdef in registry.providers.items() if ref in pdef.models
    ]
    if not matches:
        raise LimanError(
            f"Unknown model '{ref}', use the canonical 'provider/model' form "
            "or pass any LangChain chat model instance as llm directly"
        )
    if len(matches) > 1:
        raise LimanError(
            f"Ambiguous model alias '{ref}' ({sorted(matches)}), use the canonical 'provider/model' form"
        )
    provider = matches[0]
    logger.warning(
        "Model alias '%s' is deprecated, use the canonical name '%s/%s'",
        ref,
        provider,
        ref,
    )
    return ModelInfo(provider, ref, registry.providers[provider].models[ref].pricing)
