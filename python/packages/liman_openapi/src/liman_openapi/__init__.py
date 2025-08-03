from functools import singledispatch
from typing import Any, cast

from jsonschema_path.typing import Schema
from openapi_core import OpenAPI
from openapi_spec_validator.readers import read_from_filename
from openapi_spec_validator.shortcuts import validate

# Don't update the version manually, it is set by the build system.
__version__ = "0.1.0-a0"


@singledispatch
def load_openapi(_: Any) -> OpenAPI:
    raise NotImplementedError(
        "load_openapi() is not implemented for this type of input."
    )


@load_openapi.register(str)
def _(url_or_path: str) -> OpenAPI:
    schema = read_from_filename(url_or_path)[0]
    validate(schema)
    return OpenAPI.from_dict(schema)


@load_openapi.register(dict)
def _(input_dict: dict[str, Any]) -> OpenAPI:
    schema = cast(Schema, input_dict)
    validate(schema)
    return OpenAPI.from_dict(schema)
