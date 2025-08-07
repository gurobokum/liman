from abc import abstractmethod
from typing import Any
from uuid import UUID, uuid4

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, ConfigDict

from liman_core.base.component import Component
from liman_core.base.schemas import S
from liman_core.errors import LimanError
from liman_core.languages import LanguageCode, is_valid_language_code
from liman_core.registry import Registry


class Output(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    response: BaseMessage


class BaseNode(Component[S]):
    __slots__ = Component.__slots__ + (
        # lang
        "default_lang",
        "fallback_lang",
        # private
        "_compiled",
    )

    spec: S

    def __init__(
        self,
        spec: S,
        registry: Registry,
        *,
        initial_data: dict[str, Any] | None = None,
        yaml_path: str | None = None,
        strict: bool = False,
        default_lang: str = "en",
        fallback_lang: str = "en",
    ) -> None:
        super().__init__(
            spec,
            registry,
            initial_data=initial_data,
            yaml_path=yaml_path,
            strict=strict,
        )

        if not is_valid_language_code(default_lang):
            raise LimanError(f"Invalid default language code: {default_lang}")
        self.default_lang: LanguageCode = default_lang

        if not is_valid_language_code(fallback_lang):
            raise LimanError(f"Invalid fallback language code: {fallback_lang}")
        self.fallback_lang: LanguageCode = fallback_lang

        self._compiled = False

    def __repr__(self) -> str:
        return f"{self.spec.kind}:{self.name}"

    def generate_id(self) -> UUID:
        return uuid4()

    @abstractmethod
    def compile(self) -> None:
        """
        Compile the node. This method should be overridden in subclasses to implement specific compilation logic.
        """
        ...

    @abstractmethod
    def invoke(self, *args: Any, **kwargs: Any) -> Output: ...

    @abstractmethod
    async def ainvoke(self, *args: Any, **kwargs: Any) -> Output: ...

    @property
    def is_llm_node(self) -> bool:
        return self.spec.kind == "LLMNode"

    @property
    def is_tool_node(self) -> bool:
        return self.spec.kind == "ToolNode"
