from typing import Any, Literal, Self

from dishka import FromDishka
from pydantic import (
    BaseModel,
    ModelWrapValidatorHandler,
    ValidationInfo,
    model_validator,
)

from liman_core.base import BaseNode
from liman_core.dishka import inject
from liman_core.languages import LocalizedValue
from liman_core.registry import Registry

DEFAULT_TOOL_PROMPT_TEMPLATE = """
{func} - {description}
{triggers}
"""


class ToolArgument(BaseModel):
    name: str
    type: str
    description: LocalizedValue


class ToolNodeSpec(BaseModel):
    kind: Literal["ToolNode"] = "ToolNode"
    name: str
    description: LocalizedValue
    func: str

    arguments: list[ToolArgument] | None = None
    triggers: list[LocalizedValue] | None = None
    tool_prompt_template: LocalizedValue | None = None


class ToolNode(BaseNode):
    """
    Represents a tool node in a directed graph.
    This node can be used to execute specific tools or functions within a workflow.

    YAML example:
    ```
    kind: ToolNode
    name: get_weather
    description:
      en: |
        This tool retrieves the current weather for a specified location.
      ru: |
        Эта функция получает текущую погоду для указанного местоположения.
    func: lib.tools.get_weather
    arguments:
      - name: lat
        type: float
        description:
          en: latitude of the location
          ru: широта местоположения (latitude)
      - name: lon
        type: float
        description:
          en: longitude of the location
          ru: долгота местоположения (longitude)
    # Optionally, you can specify example triggers for the tool.
    triggers:
      en:
        - What's the weather in New York?
      ru:
        - Какая погода в Нью-Йорке?
    # Optionally, you can specify a template for the tool prompt.
    # It will allow to improve tool execution accuracy.
    # supported only {name}, {description} and {triggers} variables.
    tool_prompt_template:
      en: |
        {name} - {description}
        Examples:
          {triggers}
      ru: |
        {name} - {description}
        Примеры:
          {triggers}
    ```

    Usage:
    ```yaml
    kind: LLMNode
    ...
    tools:
      - get_weather
      - another_tool
    ```
    """

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
        self.kind = "ToolNode"

        if declaration:
            self.spec = ToolNodeSpec.model_validate(
                self.declaration,
                strict=True,
                context={"default_lang": self.default_lang},
            )
            self._init_prompts()
        registry.add(self)

    def _init_prompts(self) -> None:
        """
        Initialize prompts for the ToolNode.
        This prompts contain description for the node in different languages for system llm prompt to improve tool execution accuracy.
        """
        ...

    def _get_tool_prompt_template(self) -> None:
        """
        Get the tool prompt template from the declaration or use the default template.
        """
        ...
