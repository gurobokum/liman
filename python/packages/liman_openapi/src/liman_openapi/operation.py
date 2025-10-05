import inspect
from typing import Any, NamedTuple

import httpx

from liman_openapi.schemas import Endpoint, Ref
from liman_openapi.schemas.security import SecurityScheme


class RequestParams(NamedTuple):
    url: str
    query_params: dict[str, Any]
    headers: dict[str, Any]
    json_data: Any | None


class OpenAPIOperation:
    def __init__(
        self,
        endpoint: Endpoint,
        refs: dict[str, Ref] | None = None,
        security_schemes: list[SecurityScheme] | None = None,
        *,
        base_url: str | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.refs = refs
        self.security_schemes = security_schemes
        self.base_url = base_url

        self.__signature__ = self._create_signature()

    def __repr__(self) -> str:
        return f"liman_openapi.gen.id_{id(self)}.{self.endpoint.operation_id}"

    async def __call__(self, **kwargs: Any) -> object:
        return await self._request(**kwargs)

    def _create_signature(self) -> inspect.Signature:
        """
        Create inspection signature based on OpenAPI endpoint specification.
        """
        parameters = []

        for param in self.endpoint.parameters:
            parameters.append(
                inspect.Parameter(
                    param.name,
                    inspect.Parameter.KEYWORD_ONLY,
                    default=None if not param.required else inspect.Parameter.empty,
                )
            )

        if self.endpoint.request_body:
            parameters.append(
                inspect.Parameter(
                    self.endpoint.request_body.name,
                    inspect.Parameter.KEYWORD_ONLY,
                    default=inspect.Parameter.empty
                    if self.endpoint.request_body.required
                    else None,
                )
            )

        return inspect.Signature(parameters)

    async def _request(self, **kwargs: Any) -> object:
        method = self.endpoint.method
        url, query_params, headers, json_data = self._build_url_and_params(**kwargs)

        params = query_params if query_params else None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method, url, params=params, headers=headers, json=json_data
                )
                response.raise_for_status()
                return self._parse_response(response)
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"HTTP error occurred: {e.response.status_code} {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Request error occurred: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error occurred: {e}") from e

    def _parse_response(self, response: httpx.Response) -> object:
        content_type = response.headers.get("content-type", "").lower()

        if "application/json" in content_type:
            return response.json()
        elif "text/" in content_type:
            return response.text
        elif (
            content_type.startswith("image/")
            or content_type == "application/octet-stream"
        ):
            return response.content

        raise ValueError(
            f"Unsupported content type: {content_type}. Expected 'application/json', 'text/*', or 'image/*'."
        )

    def _build_url_and_params(self, **kwargs: Any) -> RequestParams:
        path = self.endpoint.path
        query_params: dict[str, Any] = {}
        headers: dict[str, Any] = {}
        json_data = None

        for param in self.endpoint.parameters:
            value = kwargs.get(param.name)
            if value is None and param.required:
                raise ValueError(f"Required parameter is missing: '{param.name}'")

            if value is not None:
                if param.in_ == "path":
                    path = path.replace(f"{{{param.name}}}", str(value))
                elif param.in_ == "query":
                    query_params[param.name] = value
                elif param.in_ == "header":
                    headers[param.name] = str(value)

        if self.endpoint.request_body:
            json_data = kwargs.get(self.endpoint.request_body.name)
            if json_data is None and self.endpoint.request_body.required:
                raise ValueError(
                    f"Required request body is missing: '{self.endpoint.request_body.name}'"
                )

            if json_data and "application/json" in self.endpoint.request_body.content:
                headers["Content-Type"] = "application/json"

        url = f"{self.base_url.rstrip('/')}{path}" if self.base_url else path
        return RequestParams(url, query_params, headers, json_data)
