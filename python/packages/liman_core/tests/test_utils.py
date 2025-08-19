from liman_core.utils import to_snake_case


def test_to_snake_case_simple() -> None:
    result = to_snake_case("CamelCase")

    assert result == "camel_case"


def test_to_snake_case_multiple_words() -> None:
    result = to_snake_case("LongCamelCaseString")

    assert result == "long_camel_case_string"


def test_to_snake_case_already_snake_case() -> None:
    result = to_snake_case("already_snake_case")

    assert result == "already_snake_case"


def test_to_snake_case_single_word() -> None:
    result = to_snake_case("word")

    assert result == "word"


def test_to_snake_case_single_letter() -> None:
    result = to_snake_case("A")

    assert result == "a"


def test_to_snake_case_empty_string() -> None:
    result = to_snake_case("")

    assert result == ""


def test_to_snake_case_numbers() -> None:
    result = to_snake_case("CamelCase123")

    assert result == "camel_case123"
