from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ValidationInfo, field_validator

from liman_core.errors import InvalidSpecError

from .service_account.schemas import ServiceAccountSpec


class Context(BaseModel):
    strict: bool = True
    inject: list[str]

    @field_validator("inject")
    @classmethod
    def validate_inject(cls, v: list[str]) -> list[str]:
        if not v:
            raise InvalidSpecError("inject list cannot be empty")
        return v


class AuthFieldSpec(BaseModel):
    service_account: ServiceAccountSpec | str | None = None

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
