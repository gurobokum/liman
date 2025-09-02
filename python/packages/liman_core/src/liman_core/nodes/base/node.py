from abc import abstractmethod
from typing import Any, Generic
from uuid import UUID, uuid4

from liman_core.base.component import Component
from liman_core.base.schemas import S
from liman_core.errors import LimanError
from liman_core.languages import LanguageCode, is_valid_language_code
from liman_core.nodes.base.schemas import NS
from liman_core.registry import Registry


class BaseNode(Component[S], Generic[S, NS]):
    """
    Abstract base class for all nodes in the Liman framework.

    BaseNode provides the foundation for LLM, Tool, and custom nodes.
    It handles language configuration, compilation, and execution lifecycle.
    All concrete nodes must inherit from this class and implement the
    abstract methods for their specific functionality.
    """

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
        """
        Initialize base node with specification and configuration.

        Args:
            spec: Node specification defining behavior and properties
            registry: Component registry for dependency resolution
            initial_data: Optional initial data for the component
            yaml_path: Optional path to the YAML file this node was loaded from
            strict: Whether to enforce strict validation
            default_lang: Default language code for localization
            fallback_lang: Fallback language code when default is unavailable

        Raises:
            LimanError: If language codes are invalid
        """
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
        """
        Generate unique identifier for this node instance.

        Returns:
            Randomly generated UUID for the node
        """
        return uuid4()

    @property
    def is_llm_node(self) -> bool:
        """
        Check if this node is an LLM node.

        Returns:
            True if this is an LLM node, False otherwise
        """
        return self.spec.kind == "LLMNode"

    @property
    def is_tool_node(self) -> bool:
        """
        Check if this node is a Tool node.

        Returns:
            True if this is a Tool node, False otherwise
        """
        return self.spec.kind == "ToolNode"

    @abstractmethod
    def compile(self) -> None:
        """
        Compile the node for execution.

        Prepares the node for execution by validating configuration,
        resolving dependencies, and performing any necessary setup.
        Must be implemented by concrete node classes.
        """
        ...

    @abstractmethod
    async def invoke(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute the node's primary functionality.

        Performs the main operation of the node. Implementation varies
        by node type (LLM calls, tool execution, custom logic).

        Args:
            *args: Positional arguments for node execution
            **kwargs: Keyword arguments for node execution

        Returns:
            Result of node execution, type varies by implementation
        """
        ...

    @abstractmethod
    def get_new_state(self) -> NS:
        """
        Create new state instance for this node.

        Returns:
            Fresh node state object for execution
        """
        ...
