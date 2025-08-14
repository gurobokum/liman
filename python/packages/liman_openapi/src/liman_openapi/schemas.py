from __future__ import annotations

from typing import Annotated, Any, Literal, NamedTuple, TypeAlias

from pydantic import BaseModel, Field, model_validator

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


class RequestBodySchema(BaseModel):
    content_type: str
    type_: Annotated[ParameterType | None, Field(alias="type", default=None)]
    ref: Annotated[str | None, Field(alias="$ref", default=None)]
    items: dict[str, str] | None = None


class RequestBody(BaseModel):
    name: str
    required: bool = False
    content: dict[str, dict[Literal["schema"], RequestBodySchema]]

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
                if not component:
                    raise ValueError(
                        f"Only $ref is supported in request body schema, but got: {schema}"
                    )
                name = component.split("/")[-1]
            else:
                content[key] = {**value}
        values["content"] = content
        values["name"] = name or values.get("name", "__request_body")
        return values


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

    def get_tool_arguments_spec(
        self, refs: dict[str, Ref] | None = None
    ) -> list[dict[str, Any]] | None:
        arguments = []

        for param in self.parameters:
            arguments.append(param.get_tool_argument_spec())

        if self.has_json_request_body and refs:
            ref_obj = self._get_request_body_ref_object(refs)
            if ref_obj:
                assert self.request_body is not None
                arguments.append(
                    {
                        "name": ref_obj.name,
                        "type": "object",
                        "optional": self.request_body.required,
                        "properties": [
                            property_.get_tool_parameter_spec()
                            for property_ in ref_obj.properties.values()
                        ],
                    }
                )

        return arguments if arguments else None

    @property
    def has_json_request_body(self) -> bool:
        return (
            self.request_body is not None
            and self.request_body.content is not None
            and "application/json" in self.request_body.content
            and self.request_body.content["application/json"].get("schema") is not None
        )

    def _get_request_body_ref_object(self, refs: dict[str, Ref]) -> Ref | None:
        if not self.request_body or not self.request_body.content:
            raise ValueError("Request body is not defined or does not contain content.")

        json_content = self.request_body.content.get("application/json")
        if not json_content or not json_content.get("schema"):
            return None

        schema = json_content["schema"]
        if not schema.ref:
            return None

        ref_name = schema.ref.split("/")[-1]
        return refs.get(ref_name)


class Property(BaseModel):
    name: str
    type_: Annotated[
        ParameterType | list[ParameterType] | None, Field(alias="type", default=None)
    ]
    title: str | None = None
    description: str | None = None
    required: bool = False
    example: str | int | float | None = None

    @model_validator(mode="before")
    @classmethod
    def parse(cls, values: dict[str, Any]) -> dict[str, Any]:
        keys = ["anyOf", "allOf", "oneOf"]

        for key in keys:
            if value := values.get(key):
                types, is_optional = cls._compose_type(value)
                if values.get("type"):
                    raise ValueError(
                        f"Property cannot have both 'type' and '{key}' defined."
                    )
                values["type"] = types
                values["required"] = not is_optional
                break
        return values

    @staticmethod
    def _compose_type(items: list[dict[str, Any]]) -> tuple[list[str], bool]:
        types = []
        is_optional = False
        for item in items:
            if item["type"] == "null":
                is_optional = True
                continue
            types.append(item["type"])
        return types, is_optional

    def get_tool_parameter_spec(self) -> dict[str, Any]:
        spec: dict[str, Any] = {"type": self.type_, "name": self.name}
        if self.description:
            spec["description"] = self.description
        return spec


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

    def get_tool_parameters_object(self) -> dict[str, Any]:
        properties = {}
        for prop_name, prop in self.properties.items():
            properties[prop_name] = prop.get_tool_parameter_spec()

        return {"type": "object", "properties": properties, "required": self.required}
