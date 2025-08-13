from pathlib import Path

import pytest
from pydantic import ValidationError
from ruamel.yaml.error import YAMLError

from liman_core.errors import InvalidSpecError
from liman_core.nodes.node.node import Node
from liman_core.registry import Registry

TEST_DATA_PATH = Path(__file__).parent / "data"


@pytest.fixture
def registry() -> Registry:
    return Registry()


def test_from_yaml_path_valid_file(registry: Registry) -> None:
    yaml_path = TEST_DATA_PATH / "valid_node.yaml"
    node = Node.from_yaml_path(str(yaml_path), registry)
    assert node.spec.name == "TestNode"
    assert node.spec.func == "test_function"
    assert node.spec.description
    assert node.spec.description["en"] == "Test node description"
    assert node.spec.description["ru"] == "Описание тестовой ноды"


def test_from_yaml_path_sets_yaml_path(registry: Registry) -> None:
    yaml_path = TEST_DATA_PATH / "valid_node.yaml"
    node = Node.from_yaml_path(str(yaml_path), registry)
    assert node.yaml_path == str(yaml_path)


def test_from_yaml_path_with_pathlib_path(registry: Registry) -> None:
    yaml_path = TEST_DATA_PATH / "valid_node.yaml"
    node = Node.from_yaml_path(yaml_path, registry)
    assert node.spec.name == "TestNode"
    assert node.spec.func == "test_function"
    assert node.yaml_path == str(yaml_path)


def test_from_yaml_path_strict_mode(registry: Registry) -> None:
    yaml_path = TEST_DATA_PATH / "valid_node.yaml"
    node = Node.from_yaml_path(str(yaml_path), registry, strict=True)
    assert node.strict is True


def test_from_yaml_path_custom_languages(registry: Registry) -> None:
    yaml_path = TEST_DATA_PATH / "valid_node.yaml"
    node = Node.from_yaml_path(
        str(yaml_path), registry, default_lang="ru", fallback_lang="en"
    )
    assert node.default_lang == "ru"
    assert node.fallback_lang == "en"


def test_from_yaml_path_nonexistent_file(registry: Registry) -> None:
    with pytest.raises(FileNotFoundError):
        Node.from_yaml_path("/nonexistent/path.yaml", registry)


def test_from_yaml_path_empty_file(registry: Registry) -> None:
    yaml_path = TEST_DATA_PATH / "empty.yaml"
    with pytest.raises(InvalidSpecError):
        Node.from_yaml_path(str(yaml_path), registry)


def test_from_yaml_path_malformed_yaml(registry: Registry) -> None:
    yaml_path = TEST_DATA_PATH / "malformed.yaml"
    with pytest.raises(YAMLError):
        Node.from_yaml_path(str(yaml_path), registry)


def test_from_yaml_path_invalid_node_spec(registry: Registry) -> None:
    yaml_path = TEST_DATA_PATH / "invalid_node.yaml"
    with pytest.raises(ValidationError):
        Node.from_yaml_path(str(yaml_path), registry)
