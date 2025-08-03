from pathlib import Path

import pytest
from dishka import AsyncContainer, Container
from pydantic import ValidationError
from ruamel.yaml.error import YAMLError

from liman_core.node import Node

TEST_DATA_PATH = Path(__file__).parent / "data"


def test_from_yaml_path_valid_file(
    test_containers: tuple[Container, AsyncContainer],
) -> None:
    yaml_path = TEST_DATA_PATH / "valid_node.yaml"
    node = Node.from_yaml_path(str(yaml_path))
    assert node.spec.name == "TestNode"
    assert node.spec.func == "test_function"
    assert node.spec.description
    assert node.spec.description["en"] == "Test node description"
    assert node.spec.description["ru"] == "Описание тестовой ноды"


def test_from_yaml_path_sets_yaml_path(
    test_containers: tuple[Container, AsyncContainer],
) -> None:
    yaml_path = TEST_DATA_PATH / "valid_node.yaml"
    node = Node.from_yaml_path(str(yaml_path))
    assert node.yaml_path == str(yaml_path)


def test_from_yaml_path_strict_mode(
    test_containers: tuple[Container, AsyncContainer],
) -> None:
    yaml_path = TEST_DATA_PATH / "valid_node.yaml"
    node = Node.from_yaml_path(str(yaml_path), strict=True)
    assert node.strict is True


def test_from_yaml_path_custom_languages(
    test_containers: tuple[Container, AsyncContainer],
) -> None:
    yaml_path = TEST_DATA_PATH / "valid_node.yaml"
    node = Node.from_yaml_path(str(yaml_path), default_lang="ru", fallback_lang="en")
    assert node.default_lang == "ru"
    assert node.fallback_lang == "en"


def test_from_yaml_path_nonexistent_file() -> None:
    with pytest.raises(FileNotFoundError):
        Node.from_yaml_path("/nonexistent/path.yaml")


def test_from_yaml_path_empty_file() -> None:
    yaml_path = TEST_DATA_PATH / "empty.yaml"
    with pytest.raises(ValidationError):
        Node.from_yaml_path(str(yaml_path))


def test_from_yaml_path_malformed_yaml() -> None:
    yaml_path = TEST_DATA_PATH / "malformed.yaml"
    with pytest.raises(YAMLError):
        Node.from_yaml_path(str(yaml_path))


def test_from_yaml_path_invalid_node_spec() -> None:
    yaml_path = TEST_DATA_PATH / "invalid_node.yaml"
    with pytest.raises(ValidationError):
        Node.from_yaml_path(str(yaml_path))
