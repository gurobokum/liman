from liman_core.languages import normalize_dict


def test_normalize_dict_example() -> None:
    data = {
        "intro": {"en": "Hello!", "ru": "Privet!"},
        "en": {"body": "How are you?", "bye": {"ru": "Пока", "en": "Bye"}},
        "ru": {"body": "Как дела?"},
        "subject": "Subject title",
    }
    expected = {
        "en": {
            "intro": "Hello!",
            "body": "How are you?",
            "bye": "Bye",
            "subject": "Subject title",
        },
        "ru": {
            "intro": "Privet!",
            "body": "Как дела?",
            "bye": "Пока",
        },
    }
    assert expected == normalize_dict(data)


def test_normalize_dict_with_inline_lang() -> None:
    data = {"en": "Hello!", "ru": "Привет!"}
    expected = {"en": "Hello!", "ru": "Привет!"}
    assert expected == normalize_dict(data)


def test_normalize_dict_flat() -> None:
    data = {"en": {"a": 1, "b": 2}, "ru": {"a": 3, "b": 4}}
    expected = {"en": {"a": 1, "b": 2}, "ru": {"a": 3, "b": 4}}
    assert expected == normalize_dict(data)


def test_normalize_dict_default_lang() -> None:
    data = {"a": 1, "b": 2}
    expected = {"en": {"a": 1, "b": 2}}
    assert expected == normalize_dict(data)


def test_normalize_dict_nested_with_default() -> None:
    data = {"section": {"a": 1, "b": {"ru": 2}}}
    expected = {"en": {"section": {"a": 1}}, "ru": {"section": {"b": 2}}}
    assert expected == normalize_dict(data)


def test_normalize_dict_multiple_levels() -> None:
    data = {
        "a": {"en": {"b": {"ru": "x", "en": "y"}}},
        "ru": {"c": "z"},
    }
    expected = {
        "en": {"a": {"b": "y"}},
        "ru": {"a": {"b": "x"}, "c": "z"},
    }
    assert expected == normalize_dict(data)


def test_normalize_dict_empty() -> None:
    assert dict() == normalize_dict({})
