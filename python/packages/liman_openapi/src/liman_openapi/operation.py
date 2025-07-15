from collections.abc import Awaitable
from typing import Any, TypeVar

import httpx

from liman_openapi.schemas import Endpoint, Ref

R = TypeVar("R")


class OpenAPIOperation:
    def __init__(
        self, endpoint: Endpoint, refs: dict[str, Ref] | None = None, *, is_async: bool
    ) -> None:
        self.endpoint = endpoint
        self.refs = refs
        self.is_async = is_async

    def __repr__(self) -> str:
        return f"liman_openapi.gen.id_{id(self)}.{self.endpoint.operation_id}"

    def __call__(self, *args: Any, **kwargs: Any) -> object | Awaitable[object]:
        if self.is_async:
            return self._async_impl(*args, **kwargs)
        else:
            return self._sync_impl(*args, **kwargs)

    def _sync_impl(self, *args: Any, **kwargs: Any) -> object:
        raise NotImplementedError("Synchronous implementation is not provided.")

    async def _async_impl(self, *args: Any, **kwargs: Any) -> object:
        method = self.endpoint.method
        url = self.endpoint.path
        headers: dict[str, Any] = {}

        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers)
        return response.json()
