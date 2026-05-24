from liman_core.errors import LimanError


class ExectutorError(LimanError):
    """
    Errors specific to Executor execution
    """

    code: str = "executor_error"


class ExecutorRestoreError(ExectutorError, RuntimeError):
    """
    Errors during restoring Executor state
    """

    code: str = "executor_restore_error"
