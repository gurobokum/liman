from typing import Annotated, Literal

from pydantic import ConfigDict, Field

from liman_core.base.schemas import BaseSpec


class CredentialsProviderSpec(BaseSpec):
    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    kind: Literal["CredentialsProvider"] = "CredentialsProvider"
    type_: Annotated[
        Literal["bearer", "basic", "aws", "gcp", "azure", "custom"],
        Field(alias="type"),
    ]
    func: str
