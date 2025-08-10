from typing import Literal

from langchain_core.messages import SystemMessage
from pydantic import BaseModel

from liman_core.base import BaseSpec
from liman_core.base.schemas import LangChainMessage, NodeState
from liman_core.edge.schemas import EdgeSpec
from liman_core.languages import LanguageCode, LanguagesBundle, LocalizedValue


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


class LLMNodeSpec(BaseSpec):
    kind: Literal["LLMNode"] = "LLMNode"
    name: str
    prompts: LocalizedValue
    tools: list[str] = []
    nodes: list[str | EdgeSpec] = []


class LLMNodeState(NodeState):
    """
    State for LLMNode.
    This class can be extended to add custom state attributes.
    """

    messages: list[LangChainMessage] = []
    input_: LangChainMessage | None = None
    output: LangChainMessage | None = None
