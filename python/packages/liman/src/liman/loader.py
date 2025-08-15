from pathlib import Path
from typing import Any

from liman_core.base.component import Component
from liman_core.errors import InvalidSpecError, LimanError
from liman_core.nodes.supported_types import get_node_cls
from liman_core.registry import Registry
from ruamel.yaml import YAML


class YamlLoaderError(LimanError):
    """
    Raised when there's an error loading YAML files.
    """


def load_specs_from_directory(
    directory: str | Path,
    registry: Registry,
    *,
    recursive: bool = True,
    strict: bool = False,
    patterns: list[str] | None = None,
) -> list[Component[Any]]:
    """
    Traverse directory recursively and load YAML files, creating corresponding components based on kind.

    Args:
        directory: Directory path to traverse
        registry: Registry instance for node creation
        recursive: Whether to traverse subdirectories
        strict: Whether to enforce strict validation
        patterns: File patterns to match (default: ["*.yaml", "*.yml"])

    Returns:
        List of loaded components

    Raises:
        YamlLoaderError: When there's an error loading YAML files
        FileNotFoundError: When directory doesn't exist
    """
    directory_path = Path(directory)

    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not directory_path.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")

    if patterns is None:
        patterns = ["*.yaml", "*.yml"]

    yaml_files = _find_yaml_files(directory_path, recursive, patterns)
    nodes: list[Component[Any]] = []
    errors: list[str] = []

    for yaml_file in yaml_files:
        try:
            loaded_nodes = _load_nodes_from_yaml(yaml_file, registry, strict)
            nodes.extend(loaded_nodes)
        except Exception as e:
            error_msg = f"Failed to load {yaml_file}: {e}"
            if strict:
                raise YamlLoaderError(error_msg) from e
            errors.append(error_msg)

    if errors and not strict:
        print(f"Warning: {len(errors)} files failed to load:")
        for error in errors:
            print(f"  - {error}")

    return nodes


def _find_yaml_files(
    directory: Path, recursive: bool, patterns: list[str]
) -> list[Path]:
    """
    Find YAML files in directory using multiple patterns.
    """
    yaml_files: list[Path] = []

    for pattern in patterns:
        if recursive:
            yaml_files.extend(directory.rglob(pattern))
        else:
            yaml_files.extend(directory.glob(pattern))

    # Remove duplicates and sort
    return sorted(set(yaml_files))


def _load_nodes_from_yaml(
    yaml_file: Path, registry: Registry, strict: bool
) -> list[Component[Any]]:
    """
    Load nodes from a YAML file that may contain single or multiple documents.
    """
    yaml = YAML()

    try:
        with open(yaml_file, encoding="utf-8") as fd:
            yaml_documents = list(yaml.load_all(fd))
    except Exception as e:
        raise YamlLoaderError(f"Failed to parse YAML: {e}") from e

    if not yaml_documents:
        raise InvalidSpecError("YAML file is empty")

    nodes: list[Component[Any]] = []
    errors: list[str] = []

    for i, yaml_data in enumerate(yaml_documents):
        try:
            node = _create_node_from_yaml_data(yaml_data, yaml_file, registry, strict)
            if node:
                nodes.append(node)
        except Exception as e:
            error_msg = f"Document {i + 1}: {e}"
            if strict:
                raise YamlLoaderError(
                    f"Failed to load document {i + 1} from {yaml_file}: {e}"
                ) from e
            errors.append(error_msg)

    if errors and not strict:
        print(f"Warning: {len(errors)} documents failed to load from {yaml_file}:")
        for error in errors:
            print(f"  - {error}")

    return nodes


def _create_node_from_yaml_data(
    yaml_data: Any, yaml_file: Path, registry: Registry, strict: bool
) -> Component[Any] | None:
    """
    Create a node from YAML data.
    """
    if not isinstance(yaml_data, dict):
        raise InvalidSpecError("YAML document must be a dictionary at the top level")

    kind = yaml_data.get("kind")
    if not kind:
        raise InvalidSpecError("YAML document must contain 'kind' field")

    try:
        node_cls = get_node_cls(kind)
    except ValueError as e:
        if strict:
            raise YamlLoaderError(f"Unsupported node kind '{kind}'") from e
        return None

    return node_cls.from_dict(
        yaml_data, registry, yaml_path=str(yaml_file), strict=strict
    )
