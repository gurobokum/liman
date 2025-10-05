from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, Field, model_validator

from liman_openapi.schemas.parameter import ParameterType


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
