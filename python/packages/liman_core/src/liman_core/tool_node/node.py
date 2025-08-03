import asyncio
import inspect
import sys
from collections.abc import Callable
from functools import reduce
from importlib import import_module
from typing import Any

from dishka import FromDishka
from langchain_core.messages import ToolMessage

from liman_core.base import BaseNode, Output
from liman_core.dishka import inject
from liman_core.errors import InvalidSpecError, LimanError
from liman_core.languages import LanguageCode, flatten_dict
from liman_core.registry import Registry
from liman_core.tool_node.errors import ToolExecutionError
from liman_core.tool_node.schemas import ToolNodeSpec
from liman_core.tool_node.utils import (
    ToolArgumentJSONSchema,
    noop,
    tool_arg_to_jsonschema,
)

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

DEFAULT_TOOL_PROMPT_TEMPLATE = """
{name} - {description}
{triggers}
""".strip()


class ToolNode(BaseNode[ToolNodeSpec]):
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
        spec: ToolNodeSpec,
        # injections
        registry: FromDishka[Registry],
        *,
        initial_data: dict[str, Any] | None = None,
        yaml_path: str | None = None,
        strict: bool = False,
        default_lang: str = "en",
        fallback_lang: str = "en",
    ) -> None:
        super().__init__(
            spec,
            initial_data=initial_data,
            yaml_path=yaml_path,
            strict=strict,
            default_lang=default_lang,
            fallback_lang=fallback_lang,
        )

        self.registry = registry
        self.registry.add(self)
        self._compiled = False

    def compile(self) -> None:
        # import implementation function
        if not self.spec.func:
            raise InvalidSpecError(
                f"ToolNode '{self.name}' must have a 'func' attribute defined."
            )

        try:
            func_path = self.spec.func.split(".")
            module = import_module(".".join(func_path[:-1]))
            self.func = getattr(module, func_path[-1])
        except (ImportError, ValueError) as e:
            if self.strict:
                raise InvalidSpecError(
                    f"Failed to import module for function '{self.spec.func}': {e}"
                ) from e
            self.func = noop
        self._compiled = True

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        yaml_path: str | None = None,
        strict: bool = False,
        default_lang: str = "en",
        fallback_lang: str = "en",
    ) -> Self:
        spec = ToolNodeSpec.model_validate(
            data, strict=strict, context={"default_lang": default_lang}
        )
        return cls(
            spec=spec,
            initial_data=data,
            yaml_path=yaml_path,
            strict=strict,
            default_lang=default_lang,
            fallback_lang=fallback_lang,
        )

    def set_func(self, func: Callable[..., Any]) -> None:
        """
        Set the function to be executed by the tool node.
        This function should match the signature defined in the tool node specification.
        """
        self.func = func
        self.spec.func = str(func)

    def invoke(self, tool_call: dict[str, Any]) -> Output[Any]:
        """
        Invoke the tool function with the provided arguments.

        Args:
            tool_call: Tool call dict with structure like {'name': 'tool_name', 'args': {...}, 'id': '...', 'type': 'tool_call'}

        Returns:
            Output with ToolMessage containing function result and proper tool call metadata
        """
        func = self.func
        tool_call_id = tool_call["id"]
        tool_call_name = tool_call["name"]

        if "args" not in tool_call:
            raise LimanError(
                "Tool call must contain 'args' field with function arguments."
            )

        call_args = self._extract_function_args(tool_call["args"])
        try:
            if asyncio.iscoroutinefunction(func):
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                result = asyncio.run_coroutine_threadsafe(
                    func(**call_args), loop
                ).result()
            else:
                result = func(**call_args)
        except Exception as e:
            response = ToolMessage(
                content=str(e),
                tool_call_id=tool_call_id,
                name=tool_call_name,
            )
        else:
            response = ToolMessage(
                content=str(result),
                tool_call_id=tool_call_id,
                name=tool_call_name,
            )
        return Output(response=response)

    async def ainvoke(self, tool_call: dict[str, Any]) -> Output[Any]:
        """
        Asynchronously invoke the tool function with the provided arguments.

        Args:
            tool_call: Tool call dict with structure like {'name': 'tool_name', 'args': {...}, 'id': '...', 'type': 'tool_call'}

        Returns:
            ToolMessage with function result and proper tool call metadata
        """
        func = self.func
        tool_call_id = tool_call["id"]
        tool_call_name = tool_call["name"]

        if "args" not in tool_call:
            raise ToolExecutionError(
                "Tool call must contain 'args' field with function arguments."
            )

        call_args = self._extract_function_args(tool_call["args"])
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(**call_args)
            else:
                result = func(**call_args)
        except Exception as e:
            response = ToolMessage(
                content=str(e),
                tool_call_id=tool_call_id,
                name=tool_call_name,
            )
        else:
            response = ToolMessage(
                content=str(result),
                tool_call_id=tool_call_id,
                name=tool_call_name,
            )
        return Output(response=response)

    def _extract_function_args(self, args_dict: dict[str, Any]) -> dict[str, Any]:
        """
        Extract function arguments based on function signature from provided args dict.

        Args:
            args_dict: Dictionary containing all available arguments

        Returns:
            Dictionary with only the arguments that match function signature
        """
        if not hasattr(self, "func") or self.func is None:
            return args_dict

        sig = inspect.signature(self.func)
        filtered_args = {}

        for param_name, param in sig.parameters.items():
            if param_name in args_dict:
                filtered_args[param_name] = args_dict[param_name]
            elif param.default is not inspect.Parameter.empty:
                continue
            else:
                raise ValueError(f"Required parameter is missing: '{param_name}'")

        return filtered_args

    def get_tool_description(self, lang: LanguageCode) -> str:
        template = self._get_tool_prompt_template(lang)

        description = self.spec.description.get(lang) or self.spec.description.get(
            self.fallback_lang, ""
        )
        if isinstance(description, dict):
            # Flatten the description dictionary if it contains nested structures
            description = flatten_dict(description)

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

        desc = self.spec.description.get(lang)
        if not desc:
            # Fallback to the default language if the specified language is not available
            desc = self.spec.description.get(self.fallback_lang)
            if not desc:
                raise InvalidSpecError("Spec doesn't have a description.")
        if isinstance(desc, dict):
            # Flatten the description dictionary if it contains nested structures
            desc = flatten_dict(desc)

        args = [
            tool_arg_to_jsonschema(arg, self.default_lang, self.fallback_lang)
            for arg in self.spec.arguments or []
        ]
        properties: dict[str, ToolArgumentJSONSchema] = reduce(
            lambda acc, arg: acc | arg, args, {}
        )

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": desc,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": [
                        arg.name
                        for arg in self.spec.arguments or []
                        if not arg.optional
                    ],
                },
            },
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
