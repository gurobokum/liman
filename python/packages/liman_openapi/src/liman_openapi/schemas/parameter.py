from __future__ import annotations

from typing import Annotated, Any, Literal, TypeAlias

from pydantic import BaseModel, Field

ParameterType: TypeAlias = Literal[
    "string", "integer", "array", "object", "null", "boolean"
]


class ParameterSchema(BaseModel):
    type_: Annotated[ParameterType, Field(alias="type")]
    format_: Annotated[str | None, Field(alias="format", default=None)]
    title: str | None = None


class Parameter(BaseModel):
    name: str
    description: str | None = None
    in_: Annotated[str, Field(alias="in")]  # 'query', 'header', 'path', 'cookie'
    required: bool = False
    schema_: Annotated[ParameterSchema, Field(alias="schema")]

    def get_json_schema(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description}

    def get_tool_argument_spec(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.schema_.type_,
            "description": self.description,
            "optional": not self.required,
        }
