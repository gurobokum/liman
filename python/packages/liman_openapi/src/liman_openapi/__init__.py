from functools import singledispatch
from typing import Any, cast

from jsonschema_path.typing import Schema
from openapi_spec_validator.readers import read_from_filename
from openapi_spec_validator.shortcuts import validate


@singledispatch
def load_openapi(_: Any) -> Schema:
    raise NotImplementedError(
        "load_openapi() is not implemented for this type of input."
    )


@load_openapi.register(str)
def _(url_or_path: str) -> Schema:
    schema = read_from_filename(url_or_path)[0]
    validate(schema)
    return schema


@load_openapi.register(dict)
def _(input_dict: dict[str, Any]) -> Schema:
    schema = cast(Schema, input_dict)
    validate(schema)
    return schema
