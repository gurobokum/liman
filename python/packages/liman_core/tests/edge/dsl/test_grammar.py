import pytest
from lark import ParseError

from liman_core.edge.dsl.grammar import when_parser


def test_when_parser_boolean_literals() -> None:
    tree = when_parser.parse("true")
    assert tree is not None

    tree = when_parser.parse("false")
    assert tree is not None


def test_when_parser_string_literals() -> None:
    tree = when_parser.parse('"hello"')
    assert tree is not None

    tree = when_parser.parse("'world'")
    assert tree is not None


def test_when_parser_number_literals() -> None:
    tree = when_parser.parse("42")
    assert tree is not None

    tree = when_parser.parse("-3.14")
    assert tree is not None


def test_when_parser_variables() -> None:
    tree = when_parser.parse("variable_name")
    assert tree is not None

    tree = when_parser.parse("snake_case_var")
    assert tree is not None


def test_when_parser_comparison_operations() -> None:
    tree = when_parser.parse("x == y")
    assert tree is not None

    tree = when_parser.parse("a != b")
    assert tree is not None

    tree = when_parser.parse("value > 10")
    assert tree is not None

    tree = when_parser.parse("count < 100")
    assert tree is not None


def test_when_parser_logical_operations() -> None:
    tree = when_parser.parse("x && y")
    assert tree is not None

    tree = when_parser.parse("a and b")
    assert tree is not None

    tree = when_parser.parse("x || y")
    assert tree is not None

    tree = when_parser.parse("a or b")
    assert tree is not None


def test_when_parser_not_operations() -> None:
    tree = when_parser.parse("!x")
    assert tree is not None

    tree = when_parser.parse("not y")
    assert tree is not None


def test_when_parser_complex_expressions() -> None:
    tree = when_parser.parse("(x == 10) && (y != 20)")
    assert tree is not None

    tree = when_parser.parse("!active or status == 'ready'")
    assert tree is not None


def test_when_parser_function_references() -> None:
    tree = when_parser.parse("module.function")
    assert tree is not None

    tree = when_parser.parse("utils.helper.check")
    assert tree is not None


def test_when_parser_invalid_syntax() -> None:
    with pytest.raises(ParseError):
        when_parser.parse("invalid syntax here")

    with pytest.raises(ParseError):
        when_parser.parse("x ==")

    with pytest.raises(ParseError):
        when_parser.parse("&& y")
