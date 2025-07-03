from typing import Any

from dishka import FromDishka

from liman_core.base import BaseNode
from liman_core.dishka import inject
from liman_core.errors import InvalidSpecError
from liman_core.languages import LanguageCode
from liman_core.registry import Registry
from liman_core.tool_node.schemas import ToolNodeSpec
from liman_core.tool_node.utils import tool_arg_to_jsonschema

DEFAULT_TOOL_PROMPT_TEMPLATE = """
{name} - {description}
{triggers}
""".strip()


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

        self.registry = registry
        self.registry.add(self)

    def get_tool_description(self, lang: LanguageCode) -> str:
        template = self._get_tool_prompt_template(lang)

        description = self.spec.description.get(lang) or self.spec.description.get(
            self.fallback_lang, ""
        )

        triggers = [
            trigger.get(lang) or trigger.get(self.fallback_lang, "")
            for trigger in (self.spec.triggers or [])
        ]
        triggers_str = "\n".join(
            f"- {trigger}" for trigger in triggers if trigger.strip()
        )

        return template.format(
            name=self.name,
            description=description,
            triggers=triggers_str,
        ).strip()

    def get_json_schema(self, lang: LanguageCode | None = None) -> dict[str, Any]:
        if lang is None:
            lang = self.default_lang

        description = getattr(self.spec.description, lang)
        if not description:
            # Fallback to the default language if the specified language is not available
            description = getattr(self.spec.description, self.fallback_lang)
            if not description:
                raise InvalidSpecError("Spec doesnt have a description.")

        args = [
            tool_arg_to_jsonschema(arg, self.default_lang, self.fallback_lang)
            for arg in self.spec.arguments or []
        ]

        return {
            "name": self.name,
            "description": description,
            "args": args,
        }

    def _get_tool_prompt_template(self, lang: LanguageCode) -> str:
        """
        Get the tool prompt template from the declaration or use the default template.
        """
        tool_prompt_template = self.spec.tool_prompt_template
        if not tool_prompt_template:
            return DEFAULT_TOOL_PROMPT_TEMPLATE

        if hasattr(tool_prompt_template, lang):
            template = tool_prompt_template[lang]
            if not isinstance(template, str):
                raise InvalidSpecError(
                    f"Tool prompt template for language '{lang}' must be a string, got {type(template).__name__}."
                )
            return template

        if hasattr(tool_prompt_template, self.fallback_lang):
            template = tool_prompt_template[self.fallback_lang]
            if not isinstance(template, str):
                raise InvalidSpecError(
                    f"Tool prompt template for fallback language '{self.fallback_lang}' must be a string, got {type(template).__name__}."
                )

        return DEFAULT_TOOL_PROMPT_TEMPLATE
