from importlib import import_module
from typing import Any

from liman_core.edge.dsl.transformer import (
    ComparisonNode,
    ConditionalExprNode,
    ExprNode,
    FunctionRefNode,
    LogicalNode,
    NotNode,
    ValueNode,
    VarNode,
    WhenExprNode,
)
from liman_core.errors import InvalidSpecError


class ConditionalEvaluator:
    """
    Evaluates conditional expressions from the edge DSL

    """

    def __init__(self, context: dict[str, Any], state_context: dict[str, Any]) -> None:
        self.context = context
        self.state_context = state_context

    def evaluate(self, expr: WhenExprNode) -> bool:
        """
        Evaluate a when expression
        """
        match expr:
            case ConditionalExprNode(expr=expr_data):
                return self._evaluate_conditional(expr_data)
            case FunctionRefNode(dotted_name=dotted_name):
                return self._evaluate_function_ref(dotted_name)

    def _evaluate_conditional(self, expr: ExprNode) -> bool:
        """
        Evaluate a conditional expression using pattern matching
        """
        match expr:
            case bool():
                return expr

            case str() | float():
                return bool(expr)

            case VarNode():
                return self._evaluate_variable(expr)

            case NotNode():
                return not self._evaluate_conditional(expr.expr)

            case ComparisonNode():
                return self._evaluate_comparison(expr)

            case LogicalNode():
                return self._evaluate_logical(expr)

            case _:
                raise ValueError(f"Unknown expression: {expr}")

    def _evaluate_variable(self, var_node: VarNode) -> bool:
        """
        Evaluate a variable reference
        """
        resolved_value = self._resolve_variable(var_node.name)
        return bool(resolved_value)

    def _evaluate_comparison(self, comp_node: ComparisonNode) -> bool:
        """
        Evaluate a comparison expression
        """
        left_val = self._resolve_operand(comp_node.left)
        right_val = self._resolve_operand(comp_node.right)

        match comp_node.type_:
            case "==":
                return bool(left_val == right_val)
            case "!=":
                return bool(left_val != right_val)
            case ">":
                return bool(left_val > right_val)
            case "<":
                return bool(left_val < right_val)
            case _:
                raise ValueError(f"Unknown comparison operator: {comp_node.type_}")

    def _evaluate_logical(self, logical_node: LogicalNode) -> bool:
        """
        Evaluate a logical expression
        """
        match logical_node.type_:
            case "and" | "&&":
                return self._evaluate_conditional(
                    logical_node.left
                ) and self._evaluate_conditional(logical_node.right)

            case "or" | "||":
                return self._evaluate_conditional(
                    logical_node.left
                ) or self._evaluate_conditional(logical_node.right)
            case _:
                raise ValueError(f"Unknown logical operator: {logical_node.type_}")

    def _resolve_operand(self, operand: ValueNode) -> Any:
        """
        Resolve an operand (variable or literal value)
        """
        match operand:
            case VarNode(name=var_name):
                return self._resolve_variable(var_name)
            case _:
                return operand

    def _evaluate_function_ref(self, func_ref: str) -> bool:
        """
        Evaluate a function reference by importing and executing it
        """
        try:
            func_path = func_ref.split(".")
            module = import_module(".".join(func_path[:-1]))
            func = getattr(module, func_path[-1])

            result = func()
            return bool(result)
        except (ImportError, AttributeError) as e:
            raise InvalidSpecError(
                f"Failed to import or execute function '{func_ref}': {e}"
            ) from e
        except Exception as e:
            raise ValueError(f"Function execution failed '{func_ref}': {e}") from e

    def _resolve_variable(self, var_name: str) -> Any:
        """
        Resolve variable name to value with support for $-prefixed variables
        """
        if var_name.startswith("$"):
            if var_name in self.context:
                return self.context[var_name]
            else:
                raise KeyError(f"Variable '{var_name}' not found in context")
        else:
            if var_name in self.state_context:
                return self.state_context[var_name]
            elif var_name in self.context:
                return self.context[var_name]
            else:
                raise KeyError(
                    f"Variable '{var_name}' not found in context or state.context"
                )
