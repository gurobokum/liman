from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ExecutorStatus(str, Enum):
    """
    Status of an executor in the tree
    """

    IDLE = "idle"
    RUNNING = "running"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutorInput(BaseModel):
    execution_id: UUID
    node_actor_id: UUID
    node_input: Any
    node_full_name: str


class ExecutorOutput(BaseModel):
    execution_id: UUID
    node_actor_id: UUID
    node_full_name: str
    node_output: Any | None = None

    exit_: bool = False

    error: str | None = None
    error_type: str | None = None


class ExecutorState(BaseModel):
    """
    Executor state that can restore the execution tree structure.

    Root Executor (01a1dd9a-9374-44e7-b8a8-7fc891b29de0) - SUSPENDED
      ├── Child Executor 1 (child1) - SUSPENDED
      ├── Child Executor 2 (cda81fa7-75f1-4800-bc2b-3aae70aa0e60) - SUSPENDED
      │     ├── Sub Executor 3 (f1e2d3c4-5678-90ab-cdef-1234567890ab) - COMPLETED
      │     └── Sub Executor 4 (a1b2c3d4-5678-90ab-cdef-1234567890ab) - RUNNING
      └── Child Executor 3 (b1c2d3e4-5678-90ab-cdef-1234567890ab) - RUNNING

    """

    execution_id: UUID
    node_actor_id: UUID

    status: ExecutorStatus

    child_executor_ids: set[UUID] = set()
