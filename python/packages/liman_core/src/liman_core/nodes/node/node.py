from collections.abc import Sequence
from typing import Any

from langchain_core.messages import BaseMessage

from liman_core.errors import LimanError
from liman_core.nodes.base.node import BaseNode
from liman_core.nodes.node.schemas import NodeSpec, NodeState
from liman_core.registry import Registry


class Node(BaseNode[NodeSpec, NodeState]):
    """
    Generic custom node for implementing specialized logic.

    Provides a base implementation for custom nodes that don't fit
    into LLM or Tool categories. Currently a placeholder implementation.
    """

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
        """
        Initialize custom node with specification and registry.

        Args:
            spec: Node specification defining custom node configuration
            registry: Component registry for dependency resolution
            initial_data: Optional initial data for the component
            yaml_path: Optional path to the YAML file this node was loaded from
            strict: Whether to enforce strict validation
            default_lang: Default language code for localization
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

    def compile(self) -> None:
        """
        Compile the custom node for execution.

        Performs basic validation and preparation for execution.

        Raises:
            LimanError: If the node is already compiled
        """
        if self._compiled:
            raise LimanError("Node is already compiled")

        self._compiled = True

    async def invoke(
        self, inputs: Sequence[BaseMessage], state: dict[str, Any], **kwargs: Any
    ) -> Any:
        """
        Execute the custom node logic.

        Currently not implemented - placeholder for future custom node logic.

        Args:
            inputs: Sequence of input messages
            state: Current execution state
            **kwargs: Additional keyword arguments

        Returns:
            Result of node execution

        Raises:
            NotImplementedError: Method is not yet implemented
        """
        raise NotImplementedError("Node.ainvoke() is not implemented yet")

    def get_new_state(self) -> NodeState:
        """
        Create new state instance for this custom node.

        Returns:
            Fresh NodeState with empty message history
        """
        return NodeState(name=self.spec.name, messages=[])
