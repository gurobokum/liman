import json
from collections.abc import Hashable, Mapping
from functools import singledispatch
from typing import Any, cast
from urllib.request import urlopen

from jsonschema_path.typing import Schema
from openapi_core import OpenAPI
from openapi_spec_validator.readers import read_from_filename
from openapi_spec_validator.shortcuts import validate
from ruamel.yaml import YAML

from liman_openapi.utils import is_url


@singledispatch
def load_openapi(_: Any) -> OpenAPI:
    raise NotImplementedError(
        "load_openapi() is not implemented for this type of input."
    )


@load_openapi.register(str)
def _(url_or_path: str) -> OpenAPI:
    if is_url(url_or_path):
        schema = _read_from_url(url_or_path)
    else:
        schema = read_from_filename(url_or_path)[0]

    validate(schema)
    return OpenAPI.from_dict(schema)


@load_openapi.register(dict)
def _(input_dict: dict[str, Any]) -> OpenAPI:
    schema = cast(Schema, input_dict)
    validate(schema)
    return OpenAPI.from_dict(schema)


def _read_from_url(url: str) -> Mapping[Hashable, Any]:
    """
    Read and parse OpenAPI spec from URL.
    """
    with urlopen(url) as response:
        content = response.read().decode("utf-8")

    try:
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError(f"Cannot parse OpenAPI spec as json from URL: {url}")
        return data
    except Exception:
        ...

    yaml = YAML(typ="safe")
    data = yaml.load(content)
    if not data:
        raise ValueError(f"Failed to parse OpenAPI spec from URL: {url}")
    if not isinstance(data, dict):
        raise ValueError(f"Failed to parse OpenAPI spec from URL: {url}")
    return data
