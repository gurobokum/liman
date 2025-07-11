from typing import Any, Literal
from uuid import uuid4

from dishka import FromDishka
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage
from pydantic import BaseModel

from liman_core.base import BaseNode, Output
from liman_core.dishka import inject
from liman_core.errors import LimanError
from liman_core.languages import (
    LanguageCode,
    LanguagesBundle,
    LocalizedValue,
)
from liman_core.registry import Registry
from liman_core.tool_node.node import ToolNode


class LLMNodeSpec(BaseModel):
    kind: Literal["LLMNode"] = "LLMNode"
    name: str
    prompts: LocalizedValue
    tools: list[str] = []


class LLMPrompts(BaseModel):
    system: str | None = None


class LLMPromptsBundle(LanguagesBundle[LLMPrompts]):
    def to_system_message(self, lang: LanguageCode) -> SystemMessage:
        """
        Convert the prompts for a specific language to a SystemMessage.
        """
        if lang not in self.__class__.model_fields:
            lang = self.fallback_lang

        prompts = getattr(self, lang, None)
        if not prompts:
            prompts = getattr(self, self.fallback_lang, None)
        return SystemMessage(content=prompts.system if prompts else "")


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
        "registry",
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

        self.registry = registry
        self.registry.add(self)

    def compile(self) -> None:
        self._init_prompts()

        self._compiled = True

    def generate_id(self) -> None:
        self.id = uuid4()

    def invoke(
        self, llm: BaseChatModel, lang: LanguageCode | None = None, **kwargs: Any
    ) -> None:
        raise NotImplementedError("LLMNode.invoke() is not implemented yet")

    async def ainvoke(
        self,
        llm: BaseChatModel,
        inputs: list[BaseMessage],
        lang: LanguageCode | None = None,
        **kwargs: Any,
    ) -> Output:
        lang = lang or self.default_lang

        system_message = self.prompts.to_system_message(lang)
        tools_jsonschema = []
        tools: dict[str, ToolNode] = {}

        for tool in self.spec.tools:
            tool_node = self.registry.lookup(ToolNode, tool)
            if not tool_node:
                raise LimanError(f"Tool {tool} isn't found in registry")

            tool_jsonschema = tool_node.get_json_schema(lang)
            tools_jsonschema.append(tool_jsonschema)
            tools[tool_node.name] = tool_node

        response = await llm.ainvoke(
            [
                system_message,
                *inputs,
            ],
            tools=tools_jsonschema,
            **kwargs,
        )

        next_nodes: list[tuple[BaseNode, dict[str, Any]]] = []

        if hasattr(response, "tool_calls"):
            for tool_call in getattr(response, "tool_calls", []):
                tool_name = tool_call["name"]
                next_nodes.append(
                    (
                        tools[tool_name],
                        tool_call,
                    )
                )

        output = Output(response=response, next_nodes=next_nodes)

        return output

    def _init_prompts(self) -> None:
        self.prompts = LLMPromptsBundle.model_validate(
            {**self.spec.prompts, "fallback_lang": self.fallback_lang}
        )

        supported_langs = self.spec.prompts.keys()
        tool_descs: dict[LanguageCode, list[str]] = {k: [] for k in supported_langs}

        for tool_name in self.spec.tools:
            if not isinstance(tool_name, str):
                raise ValueError(f"Tool name must be a string, got {type(tool_name)}")
            tool_name = tool_name.strip()

            tool = self.registry.lookup(ToolNode, tool_name)
            # TODO: skip if tool is not found with strict=False
            if not tool:
                raise LimanError("Tool {tool_name} isn't found")

            for lang in supported_langs:
                tool_desc = tool.get_tool_description(lang)
                tool_descs[lang].append(tool_desc)

        for lang, bundle in tool_descs.items():
            if not bundle:
                continue

            prompts = getattr(self.prompts, lang, LLMPrompts())
            prompts.system = (
                (prompts.system or "")
                + "\n"
                + "\n".join(tool_desc for tool_desc in bundle)
            )
