from typing import Annotated, Any

from pydantic import BaseModel, Field, model_validator

from liman_core.errors import InvalidSpecError
from liman_core.languages import LanguageCode, LocalizedValue
from liman_core.utils import extract_yaml_comment

SCALAR_TYPES: dict[str, str] = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
}


class SimpleField(BaseModel):
    name: str
    type_: Annotated[str | list[Any] | None, Field(alias="type")]
    description: LocalizedValue | None = None
    optional: bool = False

    def type_to_json_schema(self, type_: Any = None) -> dict[str, Any]:
        t = self.type_ if type_ is None else type_
        if t is None:
            raise InvalidSpecError(f"Field '{self.name}' has no type")
        if isinstance(t, str):
            if t not in SCALAR_TYPES:
                raise InvalidSpecError(
                    f"Unsupported type '{t}' for field '{self.name}'. Supported: {list(SCALAR_TYPES)}"
                )
            return {"type": SCALAR_TYPES[t]}
        if isinstance(t, list):
            if len(t) != 1:
                raise InvalidSpecError(
                    f"Array type for field '{self.name}' must be a single-element list, e.g. [str], [int]"
                )
            return {"type": "array", "items": self.type_to_json_schema(t[0])}
        raise InvalidSpecError(
            f"Unexpected type value for field '{self.name}': {type(t).__name__!r}"
        )

    def type_to_label(self, type_: Any = None) -> str:
        t = self.type_ if type_ is None else type_
        if isinstance(t, str):
            return SCALAR_TYPES.get(t, t)
        if isinstance(t, list) and len(t) == 1:
            return f"[{self.type_to_label(t[0])}]"
        return "object"


class ObjectField(SimpleField):
    fields: list["StructuredOutputField"] | None = None


StructuredOutputField = SimpleField | ObjectField

ObjectField.model_rebuild()


class StructuredOutputSpec(BaseModel):
    fields: list[StructuredOutputField] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _parse_raw(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {"fields": _fields_from_raw(data)}
        return data

    @classmethod
    def from_dict(
        cls, data: dict[str, Any], default_lang: str = "en"
    ) -> "StructuredOutputSpec":
        return cls.model_validate(data, context={"default_lang": default_lang})

    def to_json_schema(
        self, title: str, lang: LanguageCode, fallback_lang: LanguageCode
    ) -> dict[str, Any]:
        """
        Build a JSON Schema dict from this spec for use with structured LLM output.

        name:
            type: str
            description: your name
        bio:
            type: object
            properties:
                address:
                    type: str
                    description: your address
        """

        def build(fields: list[StructuredOutputField]) -> dict[str, Any]:
            properties: dict[str, Any] = {}
            required: list[str] = []
            for f in fields:
                prop = (
                    build(f.fields)
                    if isinstance(f, ObjectField) and f.fields
                    else f.type_to_json_schema()
                )
                desc = f.description and (
                    f.description.get(lang) or f.description.get(fallback_lang)
                )
                if desc:
                    prop = {**prop, "description": desc}
                properties[f.name] = prop
                if not f.optional:
                    required.append(f.name)
            result: dict[str, Any] = {"type": "object", "properties": properties}
            if required:
                result["required"] = required
            return result

        return {"title": title, **build(self.fields)}

    def to_prompt(self, lang: LanguageCode, fallback_lang: LanguageCode = "en") -> str:
        """
        Build a JSON-like prompt block describing the expected output structure.
        """

        def build(fields: list[StructuredOutputField], indent: str) -> None:
            for f in fields:
                if isinstance(f, ObjectField) and f.fields:
                    lines.append(f"{indent}{f.name}: {{")
                    build(f.fields, indent + "  ")
                    lines.append(f"{indent}}},")
                    continue
                field_val = f.type_to_label()
                desc = f.description and (
                    f.description.get(lang) or f.description.get(fallback_lang)
                )
                if desc:
                    field_val += f", {desc}"
                if f.optional:
                    field_val += ", optional"
                lines.append(f'{indent}{f.name}: "{field_val}",')

        lines: list[str] = ["{"]
        build(self.fields, "  ")
        lines.append("}")
        return "\n".join(lines)


def _fields_from_raw(data: dict[str, Any]) -> list[StructuredOutputField]:
    fields: list[StructuredOutputField] = []

    def is_ext_notation(value: Any) -> bool:
        if not isinstance(value, dict):
            return False
        type_ = value.get("type")
        return isinstance(type_, list) or (
            isinstance(type_, str) and type_ in SCALAR_TYPES
        )

    for key, value in data.items():
        optional = key.endswith("?")
        name = key.removesuffix("?")

        if is_ext_notation(value):
            optional = optional or bool(value.get("optional", False))
            fields.append(
                SimpleField.model_validate(
                    {
                        "name": name,
                        "type": value["type"],
                        "description": value.get("description"),
                        "optional": optional,
                    }
                )
            )
        elif isinstance(value, dict):
            fields.append(
                ObjectField.model_validate(
                    {
                        "name": name,
                        "type": None,
                        "description": extract_yaml_comment(data, key),
                        "optional": optional,
                        "fields": _fields_from_raw(value),
                    }
                )
            )
        else:
            type_ = (
                list(value)
                if hasattr(value, "__iter__") and not isinstance(value, str)
                else value
            )
            fields.append(
                SimpleField.model_validate(
                    {
                        "name": name,
                        "type": type_,
                        "description": extract_yaml_comment(data, key),
                        "optional": optional,
                    }
                )
            )

    return fields
