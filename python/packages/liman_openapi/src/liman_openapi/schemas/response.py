from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, model_validator

from liman_openapi.schemas.parameter import ParameterType


class ResponseSchema(BaseModel):
    content_type: str
    type_: Annotated[ParameterType | None, Field(alias="type", default=None)]
    ref: Annotated[str | None, Field(alias="$ref", default=None)]
    items: dict[str, str] | None = None


class Response(BaseModel):
    status_code: str  # e.g., '200', '404'
    description: str
    content: dict[
        str, dict[Literal["schema"], ResponseSchema]
    ]  # e.g., {'application/json': {'schema': ParameterSchema}}

    @model_validator(mode="before")
    @classmethod
    def inject_content_types(cls, values: dict[str, Any]) -> dict[str, Any]:
        content = {}

        for key, value in values.get("content", {}).items():
            schema = value.get("schema")
            if schema:
                content[key] = {**value, "schema": {**schema, "content_type": key}}
            else:
                content[key] = {**value}
        values["content"] = content
        return values
