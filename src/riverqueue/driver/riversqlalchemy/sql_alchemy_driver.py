from contextlib import (
    contextmanager,
)
from datetime import datetime, timezone
import json
from typing import (
    Any,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar,
    cast,
)

import sqlalchemy
from sqlalchemy.engine import Connection

from ...driver import (
    DriverProtocol,
    ExecutorProtocol,
    JobInsertParams,
    JobInsertResult,
)
from ...job import AttemptError, Job, JobState
from .dbsqlc import models, river_job, pg_misc

T = TypeVar(
    "T", river_job.JobInsertFastManyParams, river_job.JobInsertFastManyNoReturningParams
)

METADATA_KEY_SEQ_KEY = "seq_key"

SEQUENCE_APPEND_MANY = """
INSERT INTO river_job_sequence(key)
SELECT DISTINCT unnest(:seq_keys\\:\\:text[])
"""


class Executor(ExecutorProtocol):
    def __init__(self, conn: Connection):
        self.conn = conn
        self.pg_misc_querier = pg_misc.Querier(conn)
        self.job_querier = river_job.Querier(conn)

    def advisory_lock(self, key: int) -> None:
        self.pg_misc_querier.pg_advisory_xact_lock(key=key)

    def job_insert_many(self, all_params: list[JobInsertParams]) -> List[JobInsertResult]:
        res = self.job_querier.job_insert_fast_many(_build_insert_many_params(all_params))
        results = list(map(_result_from_row, res))
        self._sequence_append_many_from_results(results)
        return results

    def job_insert_many_no_returning(self, all_params: list[JobInsertParams]) -> int:
        if _has_sequence_params(all_params):
            return len(self.job_insert_many(all_params))

        res = self.job_querier.job_insert_fast_many_no_returning(_build_insert_many_no_returning_params(all_params))
        return res

    def _sequence_append_many_from_results(self, results: List[JobInsertResult]) -> None:
        seq_keys = _extract_sequence_keys(results)
        if not seq_keys:
            return

        self.conn.execute(sqlalchemy.text(SEQUENCE_APPEND_MANY), {"seq_keys": seq_keys})

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

    def __init__(self, conn: Connection):
        self.conn = conn

    @contextmanager
    def executor(self) -> Iterator[ExecutorProtocol]:
        yield Executor(self.conn)

    def unwrap_executor(self, tx) -> ExecutorProtocol:
        return Executor(tx)


def _result_from_row(row: river_job.JobInsertFastManyRow) -> JobInsertResult:
    return JobInsertResult(
        job=cast(Job, row.river_job),
        unique_skipped_as_duplicated=row.unique_skipped_as_duplicate,
    )


def _has_sequence_params(all_params: list[JobInsertParams]) -> bool:
    return any(_metadata_seq_key(insert_params.metadata) for insert_params in all_params)


def _extract_sequence_keys(results: List[JobInsertResult]) -> list[str]:
    seq_keys: list[str] = []
    seen: set[str] = set()

    for result in results:
        seq_key = _metadata_seq_key(result.job.metadata)
        if not seq_key or seq_key in seen:
            continue
        seen.add(seq_key)
        seq_keys.append(seq_key)

    return seq_keys


def _metadata_seq_key(metadata: Any) -> str | None:
    if not metadata:
        return None
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    if not isinstance(metadata, dict):
        return None

    seq_key = metadata.get(METADATA_KEY_SEQ_KEY)
    return seq_key if isinstance(seq_key, str) and seq_key else None


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
        insert_many_params.unique_key.append(insert_params.unique_key)
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
