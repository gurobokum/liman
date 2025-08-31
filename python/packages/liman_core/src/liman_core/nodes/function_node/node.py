import asyncio
import inspect
from collections.abc import Callable
from typing import Any

from liman_core.errors import LimanError
from liman_core.nodes.base.node import BaseNode
from liman_core.nodes.function_node.schemas import FunctionNodeSpec, FunctionNodeState
from liman_core.registry import Registry


class FunctionNode(BaseNode[FunctionNodeSpec, FunctionNodeState]):
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
            raise LimanError("FunctionNode is already compiled")

        self._compiled = True

    def set_func(self, func: Callable[..., Any]) -> None:
        """
        Set the function to be executed by the function node.
        """
        self.func = func
        self.spec.func = str(func)

    async def invoke(self, input_: Any, **kwargs: Any) -> Any:
        """
        Asynchronous invoke method for the FunctionNode.
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
        Get a new state for the Node.

        Returns:
            FunctionNodeState: A new instance of NodeState with the specified language.
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
