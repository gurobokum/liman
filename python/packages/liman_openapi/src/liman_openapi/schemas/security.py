from typing import Annotated, Literal

from pydantic import BaseModel, Field


class HTTPSecurityScheme(BaseModel):
    """
    HTTP authentication scheme (Basic, Bearer, etc.).

    Example:
        type: http
        scheme: bearer
        bearerFormat: JWT
    """

    type_: Annotated[Literal["http"], Field(alias="type")] = "http"
    scheme: str  # e.g., 'basic', 'bearer', 'digest'
    bearer_format: Annotated[str | None, Field(alias="bearerFormat")] = (
        None  # e.g., 'JWT'
    )
    description: str | None = None


class ApiKeySecurityScheme(BaseModel):
    """
    API Key authentication scheme.

    Example:
        type: apiKey
        in: header
        name: X-API-Key
    """

    type_: Annotated[Literal["apiKey"], Field(alias="type")] = "apiKey"
    name: str
    in_: Annotated[Literal["query", "header", "cookie"], Field(alias="in")]
    description: str | None = None


SecurityScheme = HTTPSecurityScheme | ApiKeySecurityScheme
