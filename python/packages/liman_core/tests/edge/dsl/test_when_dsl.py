import pytest

from liman_core.edge.dsl.grammar import when_parser
from liman_core.edge.dsl.transformer import WhenTransformer


@pytest.fixture
def transformer() -> WhenTransformer:
    return WhenTransformer()


def test_ce_simple_str_single_quotes(transformer: WhenTransformer) -> None:
    tree = when_parser.parse("status == 'active'")
    result = transformer.transform(tree)
    assert result == ("liman_ce", ("==", ("var", "status"), "active"))


def test_ce_simple_str_double_quotes(transformer: WhenTransformer) -> None:
    tree = when_parser.parse('name == "John Doe"')
    result = transformer.transform(tree)
    assert result == ("liman_ce", ("==", ("var", "name"), "John Doe"))


def test_ce_simple_true(transformer: WhenTransformer) -> None:
    tree = when_parser.parse("true")
    result = transformer.transform(tree)
    assert result == ("liman_ce", True)


def test_ce_simple_false(transformer: WhenTransformer) -> None:
    tree = when_parser.parse("false")
    result = transformer.transform(tree)
    assert result == ("liman_ce", False)


def test_ce_simple_eq(transformer: WhenTransformer) -> None:
    tree = when_parser.parse("value == 42")
    result = transformer.transform(tree)
    assert result == ("liman_ce", ("==", ("var", "value"), 42.0))


def test_ce_simple_neq(transformer: WhenTransformer) -> None:
    tree = when_parser.parse("value != 42")
    result = transformer.transform(tree)
    assert result == ("liman_ce", ("!=", ("var", "value"), 42.0))


def test_ce_simple_gt(transformer: WhenTransformer) -> None:
    tree = when_parser.parse("value > 42")
    result = transformer.transform(tree)
    assert result == ("liman_ce", (">", ("var", "value"), 42.0))


def test_ce_simple_lt(transformer: WhenTransformer) -> None:
    tree = when_parser.parse("value < 42")
    result = transformer.transform(tree)
    assert result == ("liman_ce", ("<", ("var", "value"), 42.0))


def test_ce_complex_and(transformer: WhenTransformer) -> None:
    tree = when_parser.parse("status == 'active' && count > 5")
    result = transformer.transform(tree)
    expected = (
        "liman_ce",
        ("and", ("==", ("var", "status"), "active"), (">", ("var", "count"), 5.0)),
    )
    assert result == expected


def test_ce_complex_or(transformer: WhenTransformer) -> None:
    tree = when_parser.parse("status == 'inactive' || count < 10")
    result = transformer.transform(tree)
    expected = (
        "liman_ce",
        (
            "or",
            ("==", ("var", "status"), "inactive"),
            ("<", ("var", "count"), 10.0),
        ),
    )
    assert result == expected


def test_ce_complex_not(transformer: WhenTransformer) -> None:
    tree = when_parser.parse("!(status == 'disabled')")
    result = transformer.transform(tree)
    expected = ("liman_ce", ("not", ("==", ("var", "status"), "disabled")))
    assert result == expected


def test_ce_parentheses_in_expressions(transformer: WhenTransformer) -> None:
    tree = when_parser.parse("(status == 'active' && count > 5) || priority == 'high'")
    result = transformer.transform(tree)
    expected = (
        "liman_ce",
        (
            "or",
            (
                "and",
                ("==", ("var", "status"), "active"),
                (">", ("var", "count"), 5.0),
            ),
            ("==", ("var", "priority"), "high"),
        ),
    )
    assert result == expected


def test_function_ref_simple(transformer: WhenTransformer) -> None:
    tree = when_parser.parse("utils.check_status")
    result = transformer.transform(tree)
    assert result == ("function_ref", "utils.check_status")


def test_function_ref_dotted(transformer: WhenTransformer) -> None:
    tree = when_parser.parse("my_app.utils.validators.check_status")
    result = transformer.transform(tree)
    assert result == ("function_ref", "my_app.utils.validators.check_status")
