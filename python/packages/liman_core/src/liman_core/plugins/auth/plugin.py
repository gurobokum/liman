from typing import Any

from liman_core.plugins.auth.schemas import AuthFieldSpec
from liman_core.plugins.core.base import Plugin


class AuthPlugin(Plugin):
    """
    AuthPlugin provides authentication and authorization context for node execution.
    """

    name = "AuthPlugin"
    applies_to = ["Node", "LLMNode", "ToolNode"]
    registered_kinds = ["ServiceAccount"]
    field_name = "auth"
    field_type = AuthFieldSpec

    def validate(self, spec_data: Any) -> Any: ...
