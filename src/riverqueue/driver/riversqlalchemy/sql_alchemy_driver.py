from contextlib import (
    asynccontextmanager,
    contextmanager,
)
from datetime import datetime, timezone
from riverqueue.driver.driver_protocol import AsyncDriverProtocol, AsyncExecutorProtocol
from sqlalchemy import Engine
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine
from typing import (
    AsyncGenerator,
    AsyncIterator,
    Iterator,
    Optional,
    cast, List, TypeVar, Type,
)

from ...driver import (
    DriverProtocol,
    ExecutorProtocol,
    JobInsertParams,
    JobInsertResult,
)
from ...job import AttemptError, Job, JobState
from .dbsqlc import models, river_job, pg_misc

T = TypeVar("T", river_job.JobInsertFastManyParams, river_job.JobInsertFastManyNoReturningParams)


class AsyncExecutor(AsyncExecutorProtocol):
    def __init__(self, conn: AsyncConnection):
        self.conn = conn
        self.pg_misc_querier = pg_misc.AsyncQuerier(conn)
        self.job_querier = river_job.AsyncQuerier(conn)

    async def advisory_lock(self, key: int) -> None:
        await self.pg_misc_querier.pg_advisory_xact_lock(key=key)

    async def job_insert_many(self, all_params: list[JobInsertParams]) -> List[JobInsertResult]:
        rows = [row async for row in self.job_querier.job_insert_fast_many(_build_insert_many_params(all_params))]
        return [_result_from_row(row) for row in rows]

    async def job_insert_many_no_returning(self, all_params: list[JobInsertParams]) -> int:
        res = await self.job_querier.job_insert_fast_many_no_returning(
            _build_insert_many_no_returning_params(all_params)
        )
        return res

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator:
        if self.conn.in_transaction():
            async with self.conn.begin_nested():
                yield
        else:
            async with self.conn.begin():
                yield


class AsyncDriver(AsyncDriverProtocol):
    """
    Client driver for SQL Alchemy.

    This variant is suitable for use with Python's asyncio (asynchronous I/O).
    """

    def __init__(self, conn: AsyncConnection | AsyncEngine):
        assert isinstance(conn, AsyncConnection) or isinstance(conn, AsyncEngine)

        self.conn = conn

    @asynccontextmanager
    async def executor(self) -> AsyncIterator[AsyncExecutorProtocol]:
        if isinstance(self.conn, AsyncEngine):
            async with self.conn.begin() as tx:
                yield AsyncExecutor(tx)
        else:
            yield AsyncExecutor(self.conn)

    def unwrap_executor(self, tx) -> AsyncExecutorProtocol:
        return AsyncExecutor(tx)


class Executor(ExecutorProtocol):
    def __init__(self, conn: Connection):
        self.conn = conn
        self.pg_misc_querier = pg_misc.Querier(conn)
        self.job_querier = river_job.Querier(conn)

    def advisory_lock(self, key: int) -> None:
        self.pg_misc_querier.pg_advisory_xact_lock(key=key)

    def job_insert_many(self, all_params: list[JobInsertParams]) -> List[JobInsertResult]:
        res = self.job_querier.job_insert_fast_many(_build_insert_many_params(all_params))
        return list(map(_result_from_row, res))

    def job_insert_many_no_returning(self, all_params: list[JobInsertParams]) -> int:
        res = self.job_querier.job_insert_fast_many_no_returning(_build_insert_many_no_returning_params(all_params))
        return res

    @contextmanager
    def transaction(self) -> Iterator[None]:
        if self.conn.in_transaction():
            with self.conn.begin_nested():
                yield
        else:
            with self.conn.begin():
                yield


class Driver(DriverProtocol):
    """
    Client driver for SQL Alchemy.
    """

    def __init__(self, conn: Connection | Engine):
        assert isinstance(conn, Connection) or isinstance(conn, Engine)

        self.conn = conn

    @contextmanager
    def executor(self) -> Iterator[ExecutorProtocol]:
        if isinstance(self.conn, Engine):
            with self.conn.begin() as tx:
                yield Executor(tx)
        else:
            yield Executor(self.conn)

    def unwrap_executor(self, tx) -> ExecutorProtocol:
        return Executor(tx)


def _result_from_row(row: river_job.JobInsertFastManyRow) -> JobInsertResult:
    return JobInsertResult(
        job=cast(Job, row.river_job),
        unique_skipped_as_duplicated=row.unique_skipped_as_duplicate,
    )


def _build_insert_many_params(
    all_params: list[JobInsertParams],
) -> river_job.JobInsertFastManyParams:
    return _build_insert_params(river_job.JobInsertFastManyParams, all_params)

def _build_insert_many_no_returning_params(
    all_params: list[JobInsertParams],
) -> river_job.JobInsertFastManyNoReturningParams:
    return _build_insert_params(river_job.JobInsertFastManyNoReturningParams, all_params)


def _build_insert_params(
    param_type: Type[T], all_params: list[JobInsertParams],
) -> T:
    insert_many_params = param_type(
        args=[],
        kind=[],
        max_attempts=[],
        metadata=[],
        priority=[],
        queue=[],
        scheduled_at=[],
        state=[],
        tags=[],
        unique_key=[],
        unique_states=[],
    )

    for insert_params in all_params:
        insert_many_params.args.append(insert_params.args)
        insert_many_params.kind.append(insert_params.kind)
        insert_many_params.max_attempts.append(insert_params.max_attempts)
        insert_many_params.metadata.append(insert_params.metadata or "{}")
        insert_many_params.priority.append(insert_params.priority)
        insert_many_params.queue.append(insert_params.queue)
        insert_many_params.scheduled_at.append(
            insert_params.scheduled_at or datetime.now(timezone.utc)
        )
        insert_many_params.state.append(cast(models.RiverJobState, insert_params.state))
        insert_many_params.tags.append(",".join(insert_params.tags))
        if insert_params.unique_key:
            insert_many_params.unique_key.append(insert_params.unique_key)
        if insert_params.unique_state:
            insert_many_params.unique_states.append(insert_params.unique_state)

    return insert_many_params


def job_from_row(row: models.RiverJob) -> Job:
    """
    Converts an internal sqlc generated row to the top level type, issuing a few
    minor transformations along the way. Timestamps are changed from local
    timezone to UTC.
    """

    # Trivial shortcut, but avoids a bunch of ternaries getting line wrapped below.
    def to_utc(t: datetime) -> datetime:
        return t.astimezone(timezone.utc)

    return Job(
        id=row.id,
        args=row.args,
        attempt=row.attempt,
        attempted_at=to_utc(row.attempted_at) if row.attempted_at else None,
        attempted_by=row.attempted_by,
        created_at=to_utc(row.created_at),
        errors=list(map(AttemptError.from_dict, row.errors)) if row.errors else None,
        finalized_at=to_utc(row.finalized_at) if row.finalized_at else None,
        kind=row.kind,
        max_attempts=row.max_attempts,
        metadata=row.metadata,
        priority=row.priority,
        queue=row.queue,
        scheduled_at=to_utc(row.scheduled_at),
        state=cast(JobState, row.state),
        tags=row.tags,
        unique_key=cast(Optional[bytes], row.unique_key),
    )
