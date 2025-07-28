import re


def to_snake_case(value: str) -> str:
    """
    Convert CamelCase to snake_case
    """
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()
