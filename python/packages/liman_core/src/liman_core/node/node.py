from collections.abc import Sequence
from typing import Any

from langchain_core.messages import BaseMessage

from liman_core.base import BaseNode, Output
from liman_core.errors import LimanError
from liman_core.node.schemas import NodeSpec
from liman_core.registry import Registry


class Node(BaseNode[NodeSpec]):
    spec_type = NodeSpec

    def __init__(
        self,
        spec: NodeSpec,
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
            default_lang=default_lang,
            fallback_lang=fallback_lang,
            strict=strict,
        )

        self.registry = registry
        self.registry.add(self)

    def compile(self) -> None:
        if self._compiled:
            raise LimanError("Node is already compiled")

        self._compiled = True

    def invoke(self, inputs: Sequence[BaseMessage], **kwargs: Any) -> Output[Any]:
        """
        Invoke method for the Node.
        """
        raise NotImplementedError("Node.invoke() is not implemented yet")

    async def ainvoke(
        self, inputs: Sequence[BaseMessage], **kwargs: Any
    ) -> Output[Any]:
        """
        Asynchronous invoke method for the Node.
        """
        raise NotImplementedError("Node.ainvoke() is not implemented yet")
