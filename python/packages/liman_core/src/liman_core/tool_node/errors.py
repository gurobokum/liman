from liman_core.errors import LimanError


class ToolExecutionError(LimanError):
    """Raised when a tool execution fails."""

    code: str = "tool_execution_error"
