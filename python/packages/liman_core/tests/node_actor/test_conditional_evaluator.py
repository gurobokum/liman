from unittest.mock import Mock, patch

import pytest

from liman_core.edge.dsl.transformer import (
    ComparisonNode,
    ConditionalExprNode,
    ExprType,
    FunctionRefNode,
    LogicalNode,
    NotNode,
    VarNode,
)
from liman_core.errors import InvalidSpecError
from liman_core.node_actor.conditional_evaluator import ConditionalEvaluator


@pytest.fixture
def evaluator() -> ConditionalEvaluator:
    context = {
        "$output": {"result": "success", "count": 10},
        "$status": "READY",
        "$state": {"kind": "TestNode", "name": "test"},
    }
    state_context = {"enabled": True, "threshold": 5, "name": "test_context"}
    return ConditionalEvaluator(context, state_context)


def test_evaluate_conditional_expr_true(evaluator: ConditionalEvaluator) -> None:
    expr = ConditionalExprNode(ExprType.LIMAN_CE, True)

    result = evaluator.evaluate(expr)

    assert result is True


def test_evaluate_conditional_expr_false(evaluator: ConditionalEvaluator) -> None:
    expr = ConditionalExprNode(ExprType.LIMAN_CE, False)

    result = evaluator.evaluate(expr)

    assert result is False


def test_evaluate_function_ref(evaluator: ConditionalEvaluator) -> None:
    func_ref = FunctionRefNode(ExprType.FUNCTION_REF, "test.module.func")

    with patch(
        "liman_core.node_actor.conditional_evaluator.import_module"
    ) as mock_import:
        mock_module = Mock()
        mock_func = Mock(return_value=True)
        mock_module.func = mock_func
        mock_import.return_value = mock_module

        result = evaluator.evaluate(func_ref)

        assert result is True


def test_evaluate_conditional_boolean_true(evaluator: ConditionalEvaluator) -> None:
    result = evaluator._evaluate_conditional(True)

    assert result is True


def test_evaluate_conditional_boolean_false(evaluator: ConditionalEvaluator) -> None:
    result = evaluator._evaluate_conditional(False)

    assert result is False


def test_evaluate_conditional_string_truthy(evaluator: ConditionalEvaluator) -> None:
    result = evaluator._evaluate_conditional("hello")

    assert result is True


def test_evaluate_conditional_string_falsy(evaluator: ConditionalEvaluator) -> None:
    result = evaluator._evaluate_conditional("")

    assert result is False


def test_evaluate_conditional_number_truthy(evaluator: ConditionalEvaluator) -> None:
    result = evaluator._evaluate_conditional(42.5)

    assert result is True


def test_evaluate_conditional_number_falsy(evaluator: ConditionalEvaluator) -> None:
    result = evaluator._evaluate_conditional(0.0)

    assert result is False


def test_evaluate_variable_truthy(evaluator: ConditionalEvaluator) -> None:
    var_node = VarNode("var", "enabled")

    result = evaluator._evaluate_variable(var_node)

    assert result is True


def test_evaluate_variable_falsy(evaluator: ConditionalEvaluator) -> None:
    var_node = VarNode("var", "threshold")
    evaluator.state_context["threshold"] = 0

    result = evaluator._evaluate_variable(var_node)

    assert result is False


def test_evaluate_not_expression(evaluator: ConditionalEvaluator) -> None:
    not_node = NotNode("not", True)

    result = evaluator._evaluate_conditional(not_node)

    assert result is False


def test_evaluate_comparison_equals_true(evaluator: ConditionalEvaluator) -> None:
    comp_node = ComparisonNode("==", VarNode("var", "threshold"), 5)

    result = evaluator._evaluate_comparison(comp_node)

    assert result is True


def test_evaluate_comparison_equals_false(evaluator: ConditionalEvaluator) -> None:
    comp_node = ComparisonNode("==", VarNode("var", "threshold"), 10)

    result = evaluator._evaluate_comparison(comp_node)

    assert result is False


def test_evaluate_comparison_not_equals(evaluator: ConditionalEvaluator) -> None:
    comp_node = ComparisonNode("!=", VarNode("var", "threshold"), 10)

    result = evaluator._evaluate_comparison(comp_node)

    assert result is True


def test_evaluate_comparison_greater_than_true(evaluator: ConditionalEvaluator) -> None:
    comp_node = ComparisonNode(">", VarNode("var", "threshold"), 3)

    result = evaluator._evaluate_comparison(comp_node)

    assert result is True


def test_evaluate_comparison_greater_than_false(
    evaluator: ConditionalEvaluator,
) -> None:
    comp_node = ComparisonNode(">", VarNode("var", "threshold"), 10)

    result = evaluator._evaluate_comparison(comp_node)

    assert result is False


def test_evaluate_comparison_less_than_true(evaluator: ConditionalEvaluator) -> None:
    comp_node = ComparisonNode("<", VarNode("var", "threshold"), 10)

    result = evaluator._evaluate_comparison(comp_node)

    assert result is True


def test_evaluate_comparison_less_than_false(evaluator: ConditionalEvaluator) -> None:
    comp_node = ComparisonNode("<", VarNode("var", "threshold"), 3)

    result = evaluator._evaluate_comparison(comp_node)

    assert result is False


def test_evaluate_comparison_unknown_operator(evaluator: ConditionalEvaluator) -> None:
    comp_node = ComparisonNode(">=", 5, 3)  # type: ignore[arg-type]

    with pytest.raises(ValueError) as exc_info:
        evaluator._evaluate_comparison(comp_node)

    assert "Unknown comparison operator: >=" in str(exc_info.value)


def test_evaluate_logical_and_true(evaluator: ConditionalEvaluator) -> None:
    logical_node = LogicalNode("and", True, True)

    result = evaluator._evaluate_logical(logical_node)

    assert result is True


def test_evaluate_logical_and_false(evaluator: ConditionalEvaluator) -> None:
    logical_node = LogicalNode("and", True, False)

    result = evaluator._evaluate_logical(logical_node)

    assert result is False


def test_evaluate_logical_and_symbol_true(evaluator: ConditionalEvaluator) -> None:
    logical_node = LogicalNode("&&", True, True)

    result = evaluator._evaluate_logical(logical_node)

    assert result is True


def test_evaluate_logical_or_true(evaluator: ConditionalEvaluator) -> None:
    logical_node = LogicalNode("or", True, False)

    result = evaluator._evaluate_logical(logical_node)

    assert result is True


def test_evaluate_logical_or_false(evaluator: ConditionalEvaluator) -> None:
    logical_node = LogicalNode("or", False, False)

    result = evaluator._evaluate_logical(logical_node)

    assert result is False


def test_evaluate_logical_or_symbol_true(evaluator: ConditionalEvaluator) -> None:
    logical_node = LogicalNode("||", False, True)

    result = evaluator._evaluate_logical(logical_node)

    assert result is True


def test_evaluate_logical_unknown_operator(evaluator: ConditionalEvaluator) -> None:
    logical_node = LogicalNode("xor", True, False)  # type: ignore[arg-type]

    with pytest.raises(ValueError) as exc_info:
        evaluator._evaluate_logical(logical_node)

    assert "Unknown logical operator: xor" in str(exc_info.value)


def test_resolve_operand_variable(evaluator: ConditionalEvaluator) -> None:
    var_node = VarNode("var", "threshold")

    result = evaluator._resolve_operand(var_node)

    assert result == 5


def test_resolve_operand_literal(evaluator: ConditionalEvaluator) -> None:
    result = evaluator._resolve_operand("literal_value")

    assert result == "literal_value"


def test_evaluate_function_ref_import_error(evaluator: ConditionalEvaluator) -> None:
    with patch("importlib.import_module", side_effect=ImportError("Module not found")):
        with pytest.raises(InvalidSpecError) as exc_info:
            evaluator._evaluate_function_ref("nonexistent.module.func")

        assert "Failed to import or execute function" in str(exc_info.value)


def test_evaluate_function_ref_attribute_error(evaluator: ConditionalEvaluator) -> None:
    with patch("importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_import.return_value = mock_module
        del mock_module.nonexistent_func

        with pytest.raises(InvalidSpecError) as exc_info:
            evaluator._evaluate_function_ref("module.nonexistent_func")

        assert "Failed to import or execute function" in str(exc_info.value)


def test_evaluate_function_ref_execution_error(evaluator: ConditionalEvaluator) -> None:
    with patch(
        "liman_core.node_actor.conditional_evaluator.import_module"
    ) as mock_import:
        mock_module = Mock()
        mock_func = Mock(side_effect=RuntimeError("Function failed"))
        mock_module.failing_func = mock_func
        mock_import.return_value = mock_module

        with pytest.raises(ValueError) as exc_info:
            evaluator._evaluate_function_ref("test.module.failing_func")

        assert "Function execution failed" in str(exc_info.value)


def test_resolve_variable_dollar_prefixed_found(
    evaluator: ConditionalEvaluator,
) -> None:
    result = evaluator._resolve_variable("$status")

    assert result == "READY"


def test_resolve_variable_dollar_prefixed_not_found(
    evaluator: ConditionalEvaluator,
) -> None:
    with pytest.raises(KeyError) as exc_info:
        evaluator._resolve_variable("$nonexistent")

    assert "Variable '$nonexistent' not found in context" in str(exc_info.value)


def test_resolve_variable_state_context_found(evaluator: ConditionalEvaluator) -> None:
    result = evaluator._resolve_variable("enabled")

    assert result is True


def test_resolve_variable_context_found(evaluator: ConditionalEvaluator) -> None:
    evaluator.context["regular_var"] = "context_value"

    result = evaluator._resolve_variable("regular_var")

    assert result == "context_value"


def test_resolve_variable_not_found(evaluator: ConditionalEvaluator) -> None:
    with pytest.raises(KeyError) as exc_info:
        evaluator._resolve_variable("nonexistent")

    assert "Variable 'nonexistent' not found in context or state.context" in str(
        exc_info.value
    )
