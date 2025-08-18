from liman_core.errors import ComponentNotFoundError, InvalidSpecError, LimanError


def test_liman_error_basic() -> None:
    error = LimanError("Test message")

    assert str(error) == "Test message"
    assert not hasattr(error, "code")
    assert error.kwargs == {}


def test_liman_error_with_code() -> None:
    error = LimanError("Test message", code="test_code")

    assert str(error) == "Test message"
    assert error.code == "test_code"
    assert error.kwargs == {}


def test_liman_error_with_kwargs() -> None:
    error = LimanError("Test message", extra="value", number=42)

    assert str(error) == "Test message"
    assert error.kwargs == {"extra": "value", "number": 42}


def test_liman_error_getitem() -> None:
    error = LimanError("Test message", extra="value", number=42)

    assert error["extra"] == "value"
    assert error["number"] == 42
    assert error["nonexistent"] is None


def test_invalid_spec_error() -> None:
    error = InvalidSpecError("Invalid specification")

    assert str(error) == "Invalid specification"
    assert error.code == "invalid_spec"
    assert isinstance(error, LimanError)


def test_component_not_found_error() -> None:
    error = ComponentNotFoundError("Component not found")

    assert str(error) == "Component not found"
    assert error.code == "component_not_found"
    assert isinstance(error, LimanError)
