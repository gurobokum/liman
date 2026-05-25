from enum import Enum
from typing import Annotated, Any
from uuid import UUID

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class ExecutorStatus(str, Enum):
    """
    Status of an executor in the tree
    """

    # Wating the task
    IDLE = "idle"
    # Executing specific Node
    RUNNING = "running"
    # Waiting child executors or Human in the Loop
    SUSPENDED = "suspended"
    # Finished fully the execution, cannot be reused
    # Can be garbage collected
    COMPLETED = "completed"
    # Executor failed
    FAILED = "failed"


class ExecutorInput(BaseModel):
    executor_id: UUID
    execution_id: UUID

    node_actor_id: UUID | None = None
    node_fullname: str
    node_input: Any

    context: dict[str, Any] | None = None


class ExecutorOutput(BaseModel):
    """
    - executor_id - unique id for the Executor
    - execution_id - trace id
    """

    executor_id: UUID
    execution_id: UUID
    node_actor_id: UUID
    node_fullname: str
    node_output: Any | None = None

    exit_: bool = False

    error: str | None = None
    error_type: str | None = None

    def __str__(self) -> str:
        if isinstance(self.node_output, str):
            return self.node_output

        elif isinstance(self.node_output, BaseMessage):
            content = self.node_output.content

            if isinstance(content, list):
                return "\n".join([str(item) for item in content])
            return content

        return str(self.node_output)


class ExecutorState(BaseModel):
    """
    Executor state that can restore the execution tree structure.

    Root Executor (01a1dd9a-9374-44e7-b8a8-7fc891b29de0) - SUSPENDED
      ├── Child Executor 1 (child1) - SUSPENDED
      ├── Child Executor 2 (cda81fa7-75f1-4800-bc2b-3aae70aa0e60) - SUSPENDED
      │     ├── Sub Executor 3 (f1e2d3c4-5678-90ab-cdef-1234567890ab) - COMPLETED
      │     ├── Sub Executor 4 (a1b2c3d4-5678-90ab-cdef-1234567890ab) - RUNNING
      │     └── Sub Executor 5 (2f52023c-4596-4fdd-bcfe-5e980bb66fb1) - IDLE
      └── Child Executor 3 (b1c2d3e4-5678-90ab-cdef-1234567890ab) - RUNNING

    """

    schema_version: int = 1

    executor_id: UUID
    node_actor_id: UUID

    execution_id: UUID | None = None
    iteration_count: int
    status: ExecutorStatus

    parent_executor_pair: tuple[UUID, UUID] | None = None
    child_executor_ids: Annotated[set[UUID], Field(default_factory=set)]
