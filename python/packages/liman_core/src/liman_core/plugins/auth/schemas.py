from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ValidationInfo, field_validator, model_validator

from liman_core.base.schemas import BaseSpec
from liman_core.errors import InvalidSpecError


class Context(BaseModel):
    strict: bool = True
    inject: list[str]

    @field_validator("inject")
    @classmethod
    def validate_inject(cls, v: list[str]) -> list[str]:
        if not v:
            raise InvalidSpecError("inject list cannot be empty")
        return v


class ServiceAccountSpec(BaseSpec):
    kind: str = "ServiceAccount"
    context: Context | None = None
    credentials_provider: str | None = None
    credentials_providers: list[str] | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_credentials_exclusive(cls, data: Any) -> Any:
        if data.get("credentials_provider") and data.get("credentials_providers"):
            raise InvalidSpecError(
                "Cannot specify both credentials_provider and credentials_providers"
            )
        return data

    @model_validator(mode="after")
    def validate_required_fields(self) -> "ServiceAccountSpec":
        has_credentials = bool(self.credentials_provider or self.credentials_providers)
        has_context = bool(self.context)

        if not has_credentials and not has_context:
            raise InvalidSpecError(
                "ServiceAccount must have either credentials_provider/credentials_providers or context"
            )

        return self


class AuthFieldSpec(BaseModel):
    service_account: str | ServiceAccountSpec | None = None

    @field_validator("service_account", mode="before")
    @classmethod
    def parse_service_account(cls, value: Any, info: ValidationInfo) -> Any:
        if value is None:
            return None

        if isinstance(value, str):
            return value

        try:
            name = value.get("name")
            if not name:
                value["name"] = f"ServiceAccount-{uuid4()}"
            return ServiceAccountSpec(**value)
        except Exception as e:
            raise InvalidSpecError(f"Invalid service_account spec: {e}") from e
