from typing import Literal

from langchain_core.messages import SystemMessage
from pydantic import BaseModel

from liman_core.base.schemas import BaseSpec
from liman_core.edge.schemas import EdgeSpec
from liman_core.languages import LanguageCode, LanguagesBundle, LocalizedValue
from liman_core.nodes.base.schemas import LangChainMessage, NodeState


class LLMPrompts(BaseModel):
    """
    Container for LLM prompts in a specific language.

    Holds system prompt and other prompt types that can be used
    to configure the language model's behavior.
    """

    system: str | None = None


class LLMPromptsBundle(LanguagesBundle[LLMPrompts]):
    """
    Multi-language bundle of LLM prompts with fallback support.

    Manages prompts across different languages and provides methods
    to retrieve prompts with automatic fallback to default language.
    """

    def to_system_message(self, lang: LanguageCode) -> SystemMessage:
        """
        Convert prompts for specified language to SystemMessage.

        Args:
            lang: Language code to retrieve prompts for

        Returns:
            SystemMessage containing the system prompt for the language
        """
        if lang not in self.__class__.model_fields:
            lang = self.fallback_lang

        prompts = getattr(self, lang, None)
        if not prompts:
            prompts = getattr(self, self.fallback_lang, None)
        return SystemMessage(content=prompts.system if prompts else "")


class LLMNodeSpec(BaseSpec):
    """
    Specification schema for LLM nodes.

    Defines the structure and configuration for LLM nodes including
    prompts, tools, and connected nodes.
    """

    kind: Literal["LLMNode"] = "LLMNode"
    name: str
    prompts: LocalizedValue
    tools: list[str] = []
    nodes: list[str | EdgeSpec] = []


class LLMNodeState(NodeState):
    """
    Runtime state for LLM nodes.

    Maintains conversation history, current input/output messages,
    and other state data specific to LLM node execution.
    """

    messages: list[LangChainMessage] = []
    input_: LangChainMessage | None = None
    output: LangChainMessage | None = None
