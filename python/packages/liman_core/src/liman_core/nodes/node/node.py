from collections.abc import Sequence
from typing import Any

from langchain_core.messages import BaseMessage

from liman_core.errors import LimanError
from liman_core.nodes.base.node import BaseNode
from liman_core.nodes.base.schemas import NodeOutput
from liman_core.nodes.node.schemas import NodeSpec, NodeState
from liman_core.registry import Registry


class Node(BaseNode[NodeSpec, NodeState]):
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

    def invoke(
        self, inputs: Sequence[BaseMessage], state: dict[str, Any], **kwargs: Any
    ) -> NodeOutput:
        """
        Invoke method for the Node.
        """
        raise NotImplementedError("Node.invoke() is not implemented yet")

    async def ainvoke(
        self, inputs: Sequence[BaseMessage], state: dict[str, Any], **kwargs: Any
    ) -> NodeOutput:
        """
        Asynchronous invoke method for the Node.
        """
        raise NotImplementedError("Node.ainvoke() is not implemented yet")

    def get_new_state(self) -> NodeState:
        """
        Get a new state for the Node.

        Returns:
            NodeState: A new instance of NodeState with the specified language.
        """
        return NodeState(messages=[])
