from typing import Any

from pydantic import BaseModel, field_validator


class EdgeSpec(BaseModel):
    ref: str
    when: str | None = None

    @field_validator("ref")
    @classmethod
    def validate_ref(cls, value: str) -> str:
        match value.split("/"):
            case ["ToolNode", _]:
                raise ValueError(
                    f"ToolNode cannot be an edge target, use the 'tools' field instead: '{value}'"
                )
            case [kind, name] if kind and name:
                return value
        raise ValueError(f"Invalid edge ref, expected 'Kind/name': '{value}'")

    @property
    def kind(self) -> str:
        return self.ref.split("/", 1)[0]

    @property
    def name(self) -> str:
        return self.ref.split("/", 1)[1]


def check_exclusive_routing(spec: Any) -> None:
    """
    Reject specs that mix the canonical 'to' field with 'nodes'/'llm_nodes'.
    """
    if not getattr(spec, "to", None):
        return
    used = [field for field in ("nodes", "llm_nodes") if getattr(spec, field, None)]
    if used:
        raise ValueError(
            f"Cannot mix 'to' with legacy routing fields in spec: '{spec.name}' uses {used}"
        )
