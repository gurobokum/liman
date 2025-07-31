from collections.abc import Awaitable
from typing import Any, Literal, TypeVar, overload

import httpx

from liman_openapi.schemas import Endpoint, Ref

R = TypeVar("R")


class OpenAPIOperation:
    def __init__(
        self,
        endpoint: Endpoint,
        refs: dict[str, Ref] | None = None,
        *,
        base_url: str | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.refs = refs
        self.base_url = base_url

    def __repr__(self) -> str:
        return f"liman_openapi.gen.id_{id(self)}.{self.endpoint.operation_id}"

    @overload
    def __call__(
        self, *args: Any, is_async: Literal[False] = False, **kwargs: Any
    ) -> object: ...

    @overload
    def __call__(
        self, *args: Any, is_async: Literal[True], **kwargs: Any
    ) -> Awaitable[object]: ...

    def __call__(
        self, *args: Any, is_async: bool = False, **kwargs: Any
    ) -> object | Awaitable[object]:
        return self._impl(is_async=is_async, **kwargs)

    def _impl(
        self, *, is_async: bool = False, **kwargs: Any
    ) -> object | Awaitable[object]:
        if is_async:
            return self._async_request(**kwargs)
        else:
            return self._sync_request(**kwargs)

    def _sync_request(self, **kwargs: Any) -> object:
        method = self.endpoint.method
        url, query_params, headers, json_data = self._build_url_and_params(**kwargs)

        params = query_params if query_params else None
        try:
            with httpx.Client() as client:
                response = client.request(
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

    async def _async_request(self, **kwargs: Any) -> object:
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

    def _build_url_and_params(
        self, **kwargs: Any
    ) -> tuple[str, dict[str, Any], dict[str, Any], Any]:
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
            json_data = kwargs.get("body")
            if json_data is None and self.endpoint.request_body.required:
                raise ValueError("Required request body is missing: 'body'")

            if json_data and "application/json" in self.endpoint.request_body.content:
                headers["Content-Type"] = "application/json"

        url = f"{self.base_url.rstrip('/')}{path}" if self.base_url else path
        return url, query_params, headers, json_data
