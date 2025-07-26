from typing import Annotated

from pydantic import BaseModel, Field


class EdgeSpec(BaseModel):
    target: str
    when: str | None = None
    id_: Annotated[str | None, Field(alias="id", default=None)]
    depends: list[str] | None = None
