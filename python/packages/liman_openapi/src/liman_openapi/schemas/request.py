from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, model_validator

from liman_openapi.schemas.parameter import ParameterSchema, ParameterType

ContentType = Literal["application/json", "text/plain", "text/html"]


class RequestBodySchema(BaseModel):
    content_type: ContentType
    type_: Annotated[ParameterType | None, Field(alias="type", default=None)]
    ref: Annotated[str, Field(alias="$ref")]
    items: dict[str, str] | None = None


class ParameterBodySchema(ParameterSchema):
    content_type: ContentType


class RequestBody(BaseModel):
    name: str
    required: bool = False
    content: dict[
        ContentType, dict[Literal["schema"], RequestBodySchema | ParameterBodySchema]
    ]

    @model_validator(mode="before")
    @classmethod
    def inject_content_types(cls, values: dict[str, Any]) -> dict[str, Any]:
        content = {}
        name: str | None = None
        for key, value in values.get("content", {}).items():
            schema = value.get("schema")
            if schema:
                content[key] = {**value, "schema": {**schema, "content_type": key}}
                component = schema.get("$ref")
                if component:
                    name = component.split("/")[-1]
                    values["name"] = name
            else:
                content[key] = {**value}
        values["content"] = content
        if not values.get("name"):
            values["name"] = "__request_body__"
        return values
