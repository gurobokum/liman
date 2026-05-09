from io import StringIO
from typing import Any

from ruamel.yaml import YAML

from liman_core.utils import extract_yaml_comment, to_snake_case


def _load(yaml_text: str) -> Any:
    return YAML().load(StringIO(yaml_text))


def test_extract_yaml_comment_returns_comment_for_key() -> None:
    cm = _load("a: str\n# desc for b\nb: str\n")

    assert extract_yaml_comment(cm, "b") == "desc for b"


def test_extract_yaml_comment_first_key_returns_none() -> None:
    cm = _load("a: str\n# desc for b\nb: str\n")

    assert extract_yaml_comment(cm, "a") is None


def test_extract_yaml_comment_multiline_joined_with_space() -> None:
    cm = _load("a: str\n# line one\n# line two\nb: str\n")

    assert extract_yaml_comment(cm, "b") == "line one line two"


def test_extract_yaml_comment_no_comment_returns_none() -> None:
    cm = _load("a: str\nb: str\n")

    assert extract_yaml_comment(cm, "b") is None


def test_extract_yaml_comment_unknown_key_returns_none() -> None:
    cm = _load("a: str\n# desc\nb: str\n")

    assert extract_yaml_comment(cm, "missing") is None


def test_extract_yaml_comment_plain_dict_returns_none() -> None:
    assert extract_yaml_comment({"a": "str", "b": "str"}, "b") is None


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
