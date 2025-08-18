from liman_core.edge.dsl.grammar import when_parser
from liman_core.edge.dsl.transformer import (
    ComparisonNode,
    ConditionalExprNode,
    ExprType,
    FunctionRefNode,
    LogicalNode,
    NotNode,
    VarNode,
    WhenTransformer,
)


def test_when_transformer_boolean_literals() -> None:
    transformer = WhenTransformer()
    tree = when_parser.parse("true")
    result = transformer.transform(tree)

    assert isinstance(result, ConditionalExprNode)
    assert result.type_ == ExprType.LIMAN_CE
    assert result.expr is True


def test_when_transformer_string_literals() -> None:
    transformer = WhenTransformer()
    tree = when_parser.parse('"hello"')
    result = transformer.transform(tree)

    assert isinstance(result, ConditionalExprNode)
    assert result.type_ == ExprType.LIMAN_CE
    assert result.expr == "hello"


def test_when_transformer_number_literals() -> None:
    transformer = WhenTransformer()
    tree = when_parser.parse("42")
    result = transformer.transform(tree)

    assert isinstance(result, ConditionalExprNode)
    assert result.type_ == ExprType.LIMAN_CE
    assert result.expr == 42.0


def test_when_transformer_variables() -> None:
    transformer = WhenTransformer()
    tree = when_parser.parse("variable_name")
    result = transformer.transform(tree)

    assert isinstance(result, ConditionalExprNode)
    assert result.type_ == ExprType.LIMAN_CE
    assert isinstance(result.expr, VarNode)
    assert result.expr.type_ == "var"
    assert result.expr.name == "variable_name"


def test_when_transformer_comparison_operations() -> None:
    transformer = WhenTransformer()
    tree = when_parser.parse("x == 10")
    result = transformer.transform(tree)

    assert isinstance(result, ConditionalExprNode)
    assert isinstance(result.expr, ComparisonNode)
    assert result.expr.type_ == "=="
    assert isinstance(result.expr.left, VarNode)
    assert result.expr.left.name == "x"
    assert result.expr.right == 10.0


def test_when_transformer_logical_operations() -> None:
    transformer = WhenTransformer()
    tree = when_parser.parse("x && y")
    result = transformer.transform(tree)

    assert isinstance(result, ConditionalExprNode)
    assert isinstance(result.expr, LogicalNode)
    assert result.expr.type_ == "and"
    assert isinstance(result.expr.left, VarNode)
    assert isinstance(result.expr.right, VarNode)


def test_when_transformer_not_operations() -> None:
    transformer = WhenTransformer()
    tree = when_parser.parse("!x")
    result = transformer.transform(tree)

    assert isinstance(result, ConditionalExprNode)
    assert isinstance(result.expr, NotNode)
    assert result.expr.type_ == "not"
    assert isinstance(result.expr.expr, VarNode)


def test_when_transformer_function_references() -> None:
    transformer = WhenTransformer()
    tree = when_parser.parse("module.function")
    result = transformer.transform(tree)

    assert isinstance(result, FunctionRefNode)
    assert result.type_ == ExprType.FUNCTION_REF
    assert result.dotted_name == "module.function"


def test_when_transformer_complex_expressions() -> None:
    transformer = WhenTransformer()
    tree = when_parser.parse("(x == 10) && (y != 20)")
    result = transformer.transform(tree)

    assert isinstance(result, ConditionalExprNode)
    assert isinstance(result.expr, LogicalNode)
    assert result.expr.type_ == "and"
    assert isinstance(result.expr.left, ComparisonNode)
    assert isinstance(result.expr.right, ComparisonNode)
