from typing import TypeVar

from pydantic import BaseModel


class BaseSpec(BaseModel):
    kind: str
    name: str


S = TypeVar("S", bound=BaseSpec)
