from collections.abc import Sequence
from typing import Any, cast

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

from liman_core.errors import LimanError
from liman_core.languages import LanguageCode
from liman_core.nodes.base.node import BaseNode
from liman_core.nodes.base.schemas import LangChainMessage
from liman_core.nodes.llm_node.schemas import (
    LLMNodeSpec,
    LLMNodeState,
    LLMPrompts,
    LLMPromptsBundle,
)
from liman_core.nodes.tool_node.node import ToolNode
from liman_core.registry import Registry


class LLMNode(BaseNode[LLMNodeSpec, LLMNodeState]):
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
        "prompts",
        "registry",
    )

    spec_type = LLMNodeSpec
    state_type = LLMNodeState

    def __init__(
        self,
        spec: LLMNodeSpec,
        registry: Registry,
        *,
        initial_data: dict[str, Any] | None = None,
        yaml_path: str | None = None,
        strict: bool = False,
        default_lang: str = "en",
        fallback_lang: str = "en",
    ) -> None:
        """
        Initialize LLM node with specification and registry.

        Args:
            spec: LLM node specification defining prompts and tools
            registry: Component registry for tool and dependency resolution
            initial_data: Optional initial data for the component
            yaml_path: Optional path to the YAML file this node was loaded from
            strict: Whether to enforce strict validation
            default_lang: Default language code for prompt selection
            fallback_lang: Fallback language code when default is unavailable
        """
        super().__init__(
            spec,
            registry,
            initial_data=initial_data,
            yaml_path=yaml_path,
            default_lang=default_lang,
            fallback_lang=fallback_lang,
            strict=strict,
        )

        self.registry = registry
        self.registry.add(self)

    def add_tools(self, tools: list[ToolNode]) -> None:
        """
        Add tool nodes to this LLM node for function calling.

        Args:
            tools: List of ToolNode instances to register with this LLM node

        Raises:
            TypeError: If any item in tools is not a ToolNode instance
        """
        for tool in tools:
            if not isinstance(tool, ToolNode):
                raise TypeError(f"Expected ToolNode, got {type(tool)}")
            self.spec.tools.append(tool.name)

    def compile(self) -> None:
        """
        Compile the LLM node for execution.

        Initializes prompts bundle and prepares the node for invocation.
        Must be called before invoke().

        Raises:
            LimanError: If the node is already compiled
        """
        if self._compiled:
            raise LimanError("LLMNode is already compiled")

        self._init_prompts()
        self._compiled = True

    async def invoke(
        self,
        llm: BaseChatModel,
        inputs: Sequence[BaseMessage],
        lang: LanguageCode | None = None,
        **kwargs: Any,
    ) -> LangChainMessage:
        """
        Execute the LLM node with given inputs.

        Combines system prompts with input messages and invokes the LLM
        with available tools. Returns the LLM's response message.

        Args:
            llm: Language model instance to use for generation
            inputs: Sequence of input messages for the conversation
            lang: Language code for prompt selection (uses default_lang if None)
            **kwargs: Additional arguments passed to LLM invocation

        Returns:
            Response message from the language model

        Raises:
            LimanError: If node is not compiled or tool is not found in registry
        """
        if not self._compiled:
            raise LimanError(
                "LLMNode must be compiled before invoking. Use `compile()` method."
            )

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
        )

        return cast(LangChainMessage, response)

    def get_new_state(self) -> LLMNodeState:
        """
        Create new state instance for this LLM node.

        Returns:
            Fresh LLMNodeState with empty message history
        """
        return LLMNodeState(kind=self.spec.kind, name=self.spec.name, messages=[])

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

        self.spec.prompts = cast(dict[LanguageCode, Any], self.prompts.model_dump())
