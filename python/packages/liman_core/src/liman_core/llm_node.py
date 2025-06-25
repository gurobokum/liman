from typing import Any, Literal
from uuid import uuid4

from dishka import FromDishka
from pydantic import BaseModel

from liman_core.base import BaseNode
from liman_core.dishka import inject
from liman_core.languages import (
    LanguagesBundle,
    is_valid_language_code,
    normalize_dict,
)
from liman_core.registry import Registry


class LLMNodeSpec(BaseModel):
    kind: Literal["LLMNode"] = "LLMNode"
    name: str
    prompts: dict[str, dict[str, str]] = {}
    tools: list[str] = []


class LLMPrompts(BaseModel):
    system: str | None = None


class LLMPromptsBundle(LanguagesBundle[LLMPrompts]): ...


class LLMNode(BaseNode):
    """
    Represents a node in a graph that uses a Large Language Model (LLM).

    YAML decl:
    ```yaml
    kind: LLMNode
    name: StartNode
    prompts:
      system:
        en: "You are a helpful assistant."
        ru: "Вы помощник."
    tools:
      - WeatherTool
      - EmailTool
    ```

    Language:
    Prompts can be defined in multiple languages. The `fallback_lang` is used when a specific language prompt is not available.
    Language order in prompts isn't important.
    so:
    ```yaml
    prompts:
      system:
        en: "You are a helpful assistant."
        ru: "Вы помощник."
    ```
    is equivalent to:
    ```yaml
    prompts:
    en:
      system: "You are a helpful assistant."
    ru:
      system: "Вы помощник."
    ```

    Usage:
    ```python
    LLMNode(declaration=yaml_dict, LLMNode)
    or
    LLMNode(yaml_path="llm_node.yaml")
    ```
    """

    __slots__ = BaseNode.__slots__ + (
        "kind",
        "spec",
        "prompts",
    )

    @inject
    def __init__(
        self,
        name: str,
        # injections
        registry: FromDishka[Registry],
        *,
        declaration: dict[str, Any] | None = None,
        yaml_path: str | None = None,
        default_lang: str = "en",
        fallback_lang: str = "en",
    ) -> None:
        super().__init__(
            name,
            declaration=declaration,
            yaml_path=yaml_path,
            default_lang=default_lang,
            fallback_lang=fallback_lang,
        )

        self.spec = LLMNodeSpec.model_validate(self.declaration, strict=True)
        self.kind = "LLMNode"
        registry.add(self)

    def compile(self) -> None:
        self._init_prompts()

        self._compiled = True

    def generate_id(self) -> None:
        self.id = uuid4()

    def _init_prompts(self) -> None:
        normalized_prompts = normalize_dict(self.spec.prompts, self.default_lang)
        self.prompts = LLMPromptsBundle.model_validate(
            {**normalized_prompts, "fallback_lang": self.fallback_lang}
        )
