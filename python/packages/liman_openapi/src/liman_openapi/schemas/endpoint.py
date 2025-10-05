from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, Field, model_validator

from liman_openapi.schemas.parameter import Parameter
from liman_openapi.schemas.ref import Ref
from liman_openapi.schemas.request import RequestBody, RequestBodySchema
from liman_openapi.schemas.response import Response


class Endpoint(BaseModel):
    operation_id: Annotated[str, Field(alias="operationId")]
    path: str
    summary: str
    description: str | None = None
    method: str
    parameters: list[Parameter] = []
    request_body: Annotated[
        RequestBody | None, Field(alias="requestBody", default=None)
    ]
    responses: dict[str, Response]
    security: list[dict[str, list[str]]] | None = None

    @model_validator(mode="before")
    @classmethod
    def inject_status_codes(cls, values: dict[str, Any]) -> dict[str, Any]:
        responses = values.get("responses", {})
        values["responses"] = {
            key: {"status_code": key, **value} for key, value in responses.items()
        }
        return values

    def get_tool_arguments_spec(
        self, refs: dict[str, Ref] | None = None
    ) -> list[dict[str, Any]] | None:
        arguments = []

        for param in self.parameters:
            arguments.append(param.get_tool_argument_spec())
            if self.has_json_request_body and refs:
                ref_obj = self._get_request_body_ref_object(refs)
                assert self.request_body is not None
                arguments.append(
                    {
                        "name": ref_obj.name,
                        "type": "object",
                        "optional": self.request_body.required,
                        "properties": [
                            property_.get_tool_parameter_spec()
                            for property_ in ref_obj.properties.values()
                        ],
                    }
                )

        return arguments if arguments else None

    @property
    def has_json_request_body(self) -> bool:
        return (
            self.request_body is not None
            and self.request_body.content is not None
            and "application/json" in self.request_body.content
            and self.request_body.content["application/json"].get("schema") is not None
        )

    def _get_request_body_ref_object(self, refs: dict[str, Ref]) -> Ref:
        if not self.request_body or not self.request_body.content:
            raise ValueError("Request body is not defined or does not contain content.")

        json_content = self.request_body.content.get("application/json")
        if not json_content or not json_content.get("schema"):
            raise ValueError("Request body does not contain JSON schema.")

        schema = json_content["schema"]
        if not isinstance(schema, RequestBodySchema):
            raise ValueError("Request body schema doesnt have $ref")

        ref_name = schema.ref.split("/")[-1]
        return refs[ref_name]
