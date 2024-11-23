from contextlib import (
    contextmanager,
)
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterator, List, Optional, Protocol

from ..job import Job


@dataclass
class JobInsertParams:
    """
    Insert parameters for a job. This is sent to underlying drivers and is meant
    for internal use only. Its interface is subject to change.
    """

    kind: str
    args: Any = None
    created_at: Optional[datetime] = None
    finalized_at: Optional[datetime] = None
    metadata: Optional[Any] = None
    max_attempts: int = field(default=25)
    priority: int = field(default=1)
    queue: str = field(default="default")
    scheduled_at: Optional[datetime] = None
    state: str = field(default="available")
    tags: list[str] = field(default_factory=list)
    unique_key: Optional[memoryview] = None
    unique_state: Optional[int] = None


@dataclass
class JobInsertResult:
    """
    Result of inserting a job. This is sent to underlying drivers and is meant
    for internal use only. Its interface is subject to change.
    """

    job: Job
    unique_skipped_as_duplicated: bool


class ExecutorProtocol(Protocol):
    """
    Protocol for a non-asyncio executor. An executor wraps a connection pool or
    transaction and performs the operations required for a client to insert a
    job.
    """

    def advisory_lock(self, lock: int) -> None:
        pass

    def job_insert_many(self, all_params) -> List[JobInsertResult]:
        pass

    def job_insert_many_no_returning(self, all_params) -> int:
        pass

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """
        Used as a context manager in a `with` block, open a transaction or
        subtransaction for the given context. Commits automatically on exit, or
        rolls back on error.
        """

        pass


class DriverProtocol(Protocol):
    """
    Protocol for a non-asyncio client driver. A driver acts as a layer of
    abstraction that wraps another class for a client to work.
    """

    @contextmanager
    def executor(self) -> Iterator[ExecutorProtocol]:
        """
        Used as a context manager in a `with` block, return an executor from the
        underlying engine that's good for the given context.
        """

        pass

    def unwrap_executor(self, tx) -> ExecutorProtocol:
        """
        Produces an executor from a transaction.
        """

        pass
