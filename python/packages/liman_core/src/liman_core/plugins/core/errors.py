from liman_core.errors import LimanError


class PluginConflictError(LimanError):
    """Raised when there is a conflict in plugin registration."""

    code: str = "plugin_conflict"


class PluginFieldConflictError(LimanError):
    """Raised when a plugin field already exists in the spec."""

    code: str = "plugin_field_conflict"
