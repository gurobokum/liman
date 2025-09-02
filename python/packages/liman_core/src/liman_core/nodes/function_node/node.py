import asyncio
import inspect
from collections.abc import Callable
from typing import Any

from liman_core.errors import LimanError
from liman_core.nodes.base.node import BaseNode
from liman_core.nodes.function_node.schemas import FunctionNodeSpec, FunctionNodeState
from liman_core.registry import Registry


class FunctionNode(BaseNode[FunctionNodeSpec, FunctionNodeState]):
    """
    Node for executing custom Python functions within workflows.

    FunctionNode allows integration of arbitrary Python functions
    into the Liman execution graph. Functions can be sync or async.
    """

    spec_type = FunctionNodeSpec
    state_type = FunctionNodeState

    def __init__(
        self,
        spec: FunctionNodeSpec,
        registry: Registry,
        *,
        initial_data: dict[str, Any] | None = None,
        yaml_path: str | None = None,
        strict: bool = False,
        default_lang: str = "en",
        fallback_lang: str = "en",
    ) -> None:
        """
        Initialize function node with specification and registry.

        Args:
            spec: Function node specification defining the target function
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
        Compile the function node for execution.

        Prepares the node for execution. Currently performs basic
        validation and sets the compiled flag.

        Raises:
            LimanError: If the node is already compiled
        """
        if self._compiled:
            raise LimanError("FunctionNode is already compiled")

        self._compiled = True

    def set_func(self, func: Callable[..., Any]) -> None:
        """
        Manually set the function for this function node.

        Args:
            func: Callable function to execute during invocation
        """
        self.func = func
        self.spec.func = str(func)

    async def invoke(self, input_: Any, **kwargs: Any) -> Any:
        """
        Execute the function node with provided input.

        Extracts function arguments from input and executes the function.
        Handles both synchronous and asynchronous functions.

        Args:
            input_: Input data to pass to the function
            **kwargs: Additional keyword arguments

        Returns:
            Result of function execution
        """
        func = self.func
        call_args = self._extract_function_args(input_)

        if asyncio.iscoroutinefunction(func):
            result = await func(**call_args)
        else:
            result = func(**call_args)
        return result

    def get_new_state(self) -> FunctionNodeState:
        """
        Create new state instance for this function node.

        Returns:
            Fresh FunctionNodeState with empty message history
        """
        return FunctionNodeState(name=self.spec.name, messages=[])

    def _extract_function_args(
        self, args_dict: dict[str, Any] | None
    ) -> dict[str, Any]:
        """
        Extract function arguments based on function signature from provided args dict.

        Args:
            args_dict: Dictionary containing all available arguments

        Returns:
            Dictionary with only the arguments that match function signature
        """
        if not hasattr(self, "func") or self.func is None:
            raise LimanError("func is not set for the FunctionNode")

        if not args_dict:
            return {}

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
