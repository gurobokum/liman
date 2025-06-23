from typing import Any

from liman_core.base import BaseNode


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

    def __init__(
        self,
        *,
        declaration: dict[str, Any] | None = None,
        yaml_path: str | None = None,
        default_lang: str = "en",
        fallback_lang: str = "en",
    ) -> None:
        super().__init__(
            declaration=declaration,
            yaml_path=yaml_path,
            default_lang=default_lang,
            fallback_lang=fallback_lang,
        )
        self.kind = "ToolNode"
