from typing import Annotated, Any, Literal, TypeAlias

from pydantic import BaseModel, Field, model_validator

ParameterType: TypeAlias = Literal["string", "integer", "array", "object"]


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


class RequestBodySchema(BaseModel):
    content_type: str
    type_: Annotated[ParameterType | None, Field(alias="type", default=None)]
    ref: Annotated[str | None, Field(alias="$ref", default=None)]
    items: dict[Literal["$ref"], str] | None = None


class RequestBody(BaseModel):
    required: bool = False
    content: dict[str, dict[Literal["schema"], RequestBodySchema]]

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


class ResponseSchema(BaseModel):
    content_type: str
    type_: Annotated[ParameterType | None, Field(alias="type", default=None)]
    ref: Annotated[str | None, Field(alias="$ref", default=None)]
    items: dict[Literal["$ref"], str] | None = None


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


class Endpoint(BaseModel):
    operation_id: Annotated[str, Field(alias="operationId")]
    path: str
    summary: str
    method: str
    parameters: list[Parameter] = []
    request_body: Annotated[
        RequestBody | None, Field(alias="requestBody", default=None)
    ]
    responses: dict[str, Response]

    @model_validator(mode="before")
    @classmethod
    def inject_status_codes(cls, values: dict[str, Any]) -> dict[str, Any]:
        responses = values.get("responses", {})
        values["responses"] = {
            key: {"status_code": key, **value} for key, value in responses.items()
        }
        return values

    def get_tool_arguments_spec(self) -> list[dict[str, Any]] | None:
        if not self.parameters:
            return None
        return [param.get_tool_argument_spec() for param in self.parameters]


class Property(BaseModel):
    name: str
    type_: Annotated[ParameterType, Field(alias="type")]
    description: str | None = None
    example: str | int | float | None = None


class Ref(BaseModel):
    name: str
    properties: dict[str, Property] = {}
    required: list[str] = []

    @model_validator(mode="before")
    @classmethod
    def inject_property_names(cls, values: dict[str, Any]) -> dict[str, Any]:
        props = values.get("properties", {})
        values["properties"] = {
            key: {"name": key, **value} for key, value in props.items()
        }
        return values
