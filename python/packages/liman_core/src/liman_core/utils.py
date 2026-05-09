import re
from typing import Any


def to_snake_case(value: str) -> str:
    """
    Convert CamelCase to snake_case
    """
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()


def extract_yaml_comment(cm: Any, key: str) -> str | None:
    """
    Extract before-key comment text for a key from a ruamel.yaml CommentedMap.

    ruamel.yaml stores a before-key comment at index 2 of the *previous* key's
    ca.items entry, not on the key itself. Multiline comments (multiple # lines
    in one token) are joined with a space.
    Returns None when no comment is found or cm is not a CommentedMap.
    """
    ca = getattr(cm, "ca", None)
    if ca is None:
        return None

    keys = list(cm.keys())
    idx = keys.index(key) if key in keys else -1
    if idx <= 0:
        return None

    prev_item = ca.items.get(keys[idx - 1])
    if not prev_item or not prev_item[2]:
        return None

    tokens = prev_item[2] if isinstance(prev_item[2], list) else [prev_item[2]]
    lines = []
    for token in tokens:
        if token is None:
            continue
        for line in token.value.splitlines():
            text = line.strip().lstrip("#").strip()
            if text:
                lines.append(text)

    return " ".join(lines) if lines else None
