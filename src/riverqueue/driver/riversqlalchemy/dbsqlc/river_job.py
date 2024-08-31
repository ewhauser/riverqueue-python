# Code generated by sqlc. DO NOT EDIT.
# versions:
#   sqlc v1.27.0
# source: river_job.sql
import dataclasses
import datetime
from typing import Any, AsyncIterator, Iterator, List, Optional

import sqlalchemy
import sqlalchemy.ext.asyncio

from . import models


JOB_GET_ALL = """-- name: job_get_all \\:many
SELECT id, args, attempt, attempted_at, attempted_by, created_at, errors, finalized_at, kind, max_attempts, metadata, priority, queue, state, scheduled_at, tags, unique_key
FROM river_job
"""


JOB_GET_BY_ID = """-- name: job_get_by_id \\:one
SELECT id, args, attempt, attempted_at, attempted_by, created_at, errors, finalized_at, kind, max_attempts, metadata, priority, queue, state, scheduled_at, tags, unique_key
FROM river_job
WHERE id = :p1
"""


JOB_GET_BY_KIND_AND_UNIQUE_PROPERTIES = """-- name: job_get_by_kind_and_unique_properties \\:one
SELECT id, args, attempt, attempted_at, attempted_by, created_at, errors, finalized_at, kind, max_attempts, metadata, priority, queue, state, scheduled_at, tags, unique_key
FROM river_job
WHERE kind = :p1
    AND CASE WHEN :p2\\:\\:boolean THEN args = :p3 ELSE true END
    AND CASE WHEN :p4\\:\\:boolean THEN tstzrange(:p5\\:\\:timestamptz, :p6\\:\\:timestamptz, '[)') @> created_at ELSE true END
    AND CASE WHEN :p7\\:\\:boolean THEN queue = :p8 ELSE true END
    AND CASE WHEN :p9\\:\\:boolean THEN state\\:\\:text = any(:p10\\:\\:text[]) ELSE true END
"""


@dataclasses.dataclass()
class JobGetByKindAndUniquePropertiesParams:
    kind: str
    by_args: bool
    args: Any
    by_created_at: bool
    created_at_begin: datetime.datetime
    created_at_end: datetime.datetime
    by_queue: bool
    queue: str
    by_state: bool
    state: List[str]


JOB_INSERT_FAST = """-- name: job_insert_fast \\:one
INSERT INTO river_job(
    args,
    created_at,
    finalized_at,
    kind,
    max_attempts,
    metadata,
    priority,
    queue,
    scheduled_at,
    state,
    tags
) VALUES (
    :p1\\:\\:jsonb,
    coalesce(:p2\\:\\:timestamptz, now()),
    :p3,
    :p4\\:\\:text,
    :p5\\:\\:smallint,
    coalesce(:p6\\:\\:jsonb, '{}'),
    :p7\\:\\:smallint,
    :p8\\:\\:text,
    coalesce(:p9\\:\\:timestamptz, now()),
    :p10\\:\\:river_job_state,
    coalesce(:p11\\:\\:varchar(255)[], '{}')
) RETURNING id, args, attempt, attempted_at, attempted_by, created_at, errors, finalized_at, kind, max_attempts, metadata, priority, queue, state, scheduled_at, tags, unique_key
"""


@dataclasses.dataclass()
class JobInsertFastParams:
    args: Any
    created_at: Optional[datetime.datetime]
    finalized_at: Optional[datetime.datetime]
    kind: str
    max_attempts: int
    metadata: Any
    priority: int
    queue: str
    scheduled_at: Optional[datetime.datetime]
    state: models.RiverJobState
    tags: List[str]


JOB_INSERT_FAST_MANY = """-- name: job_insert_fast_many \\:execrows
INSERT INTO river_job(
    args,
    kind,
    max_attempts,
    metadata,
    priority,
    queue,
    scheduled_at,
    state,
    tags
) SELECT
    unnest(:p1\\:\\:jsonb[]),
    unnest(:p2\\:\\:text[]),
    unnest(:p3\\:\\:smallint[]),
    unnest(:p4\\:\\:jsonb[]),
    unnest(:p5\\:\\:smallint[]),
    unnest(:p6\\:\\:text[]),
    unnest(:p7\\:\\:timestamptz[]),
    unnest(:p8\\:\\:river_job_state[]),

    -- Had trouble getting multi-dimensional arrays to play nicely with sqlc,
    -- but it might be possible. For now, join tags into a single string.
    string_to_array(unnest(:p9\\:\\:text[]), ',')
"""


@dataclasses.dataclass()
class JobInsertFastManyParams:
    args: List[Any]
    kind: List[str]
    max_attempts: List[int]
    metadata: List[Any]
    priority: List[int]
    queue: List[str]
    scheduled_at: List[datetime.datetime]
    state: List[models.RiverJobState]
    tags: List[str]


JOB_INSERT_FULL = """-- name: job_insert_full \\:one
INSERT INTO river_job(
    args,
    attempt,
    attempted_at,
    created_at,
    errors,
    finalized_at,
    kind,
    max_attempts,
    metadata,
    priority,
    queue,
    scheduled_at,
    state,
    tags,
    unique_key
) VALUES (
    :p1\\:\\:jsonb,
    coalesce(:p2\\:\\:smallint, 0),
    :p3,
    coalesce(:p4\\:\\:timestamptz, now()),
    :p5\\:\\:jsonb[],
    :p6,
    :p7\\:\\:text,
    :p8\\:\\:smallint,
    coalesce(:p9\\:\\:jsonb, '{}'),
    :p10\\:\\:smallint,
    :p11\\:\\:text,
    coalesce(:p12\\:\\:timestamptz, now()),
    :p13\\:\\:river_job_state,
    coalesce(:p14\\:\\:varchar(255)[], '{}'),
    :p15
) RETURNING id, args, attempt, attempted_at, attempted_by, created_at, errors, finalized_at, kind, max_attempts, metadata, priority, queue, state, scheduled_at, tags, unique_key
"""


@dataclasses.dataclass()
class JobInsertFullParams:
    args: Any
    attempt: int
    attempted_at: Optional[datetime.datetime]
    created_at: Optional[datetime.datetime]
    errors: List[Any]
    finalized_at: Optional[datetime.datetime]
    kind: str
    max_attempts: int
    metadata: Any
    priority: int
    queue: str
    scheduled_at: Optional[datetime.datetime]
    state: models.RiverJobState
    tags: List[str]
    unique_key: Optional[memoryview]


JOB_INSERT_UNIQUE = """-- name: job_insert_unique \\:one
INSERT INTO river_job(
    args,
    created_at,
    finalized_at,
    kind,
    max_attempts,
    metadata,
    priority,
    queue,
    scheduled_at,
    state,
    tags,
    unique_key
) VALUES (
    :p1,
    coalesce(:p2\\:\\:timestamptz, now()),
    :p3,
    :p4,
    :p5,
    coalesce(:p6\\:\\:jsonb, '{}'),
    :p7,
    :p8,
    coalesce(:p9\\:\\:timestamptz, now()),
    :p10,
    coalesce(:p11\\:\\:varchar(255)[], '{}'),
    :p12
)
ON CONFLICT (kind, unique_key) WHERE unique_key IS NOT NULL
    -- Something needs to be updated for a row to be returned on a conflict.
    DO UPDATE SET kind = EXCLUDED.kind
RETURNING id, args, attempt, attempted_at, attempted_by, created_at, errors, finalized_at, kind, max_attempts, metadata, priority, queue, state, scheduled_at, tags, unique_key, (xmax != 0) AS unique_skipped_as_duplicate
"""


@dataclasses.dataclass()
class JobInsertUniqueParams:
    args: Any
    created_at: Optional[datetime.datetime]
    finalized_at: Optional[datetime.datetime]
    kind: str
    max_attempts: int
    metadata: Any
    priority: int
    queue: str
    scheduled_at: Optional[datetime.datetime]
    state: models.RiverJobState
    tags: List[str]
    unique_key: Optional[memoryview]


@dataclasses.dataclass()
class JobInsertUniqueRow:
    id: int
    args: Any
    attempt: int
    attempted_at: Optional[datetime.datetime]
    attempted_by: Optional[List[str]]
    created_at: datetime.datetime
    errors: Optional[List[Any]]
    finalized_at: Optional[datetime.datetime]
    kind: str
    max_attempts: int
    metadata: Any
    priority: int
    queue: str
    state: models.RiverJobState
    scheduled_at: datetime.datetime
    tags: List[str]
    unique_key: Optional[memoryview]
    unique_skipped_as_duplicate: bool


class Querier:
    def __init__(self, conn: sqlalchemy.engine.Connection):
        self._conn = conn

    def job_get_all(self) -> Iterator[models.RiverJob]:
        result = self._conn.execute(sqlalchemy.text(JOB_GET_ALL))
        for row in result:
            yield models.RiverJob(
                id=row[0],
                args=row[1],
                attempt=row[2],
                attempted_at=row[3],
                attempted_by=row[4],
                created_at=row[5],
                errors=row[6],
                finalized_at=row[7],
                kind=row[8],
                max_attempts=row[9],
                metadata=row[10],
                priority=row[11],
                queue=row[12],
                state=row[13],
                scheduled_at=row[14],
                tags=row[15],
                unique_key=row[16],
            )

    def job_get_by_id(self, *, id: int) -> Optional[models.RiverJob]:
        row = self._conn.execute(sqlalchemy.text(JOB_GET_BY_ID), {"p1": id}).first()
        if row is None:
            return None
        return models.RiverJob(
            id=row[0],
            args=row[1],
            attempt=row[2],
            attempted_at=row[3],
            attempted_by=row[4],
            created_at=row[5],
            errors=row[6],
            finalized_at=row[7],
            kind=row[8],
            max_attempts=row[9],
            metadata=row[10],
            priority=row[11],
            queue=row[12],
            state=row[13],
            scheduled_at=row[14],
            tags=row[15],
            unique_key=row[16],
        )

    def job_get_by_kind_and_unique_properties(self, arg: JobGetByKindAndUniquePropertiesParams) -> Optional[models.RiverJob]:
        row = self._conn.execute(sqlalchemy.text(JOB_GET_BY_KIND_AND_UNIQUE_PROPERTIES), {
            "p1": arg.kind,
            "p2": arg.by_args,
            "p3": arg.args,
            "p4": arg.by_created_at,
            "p5": arg.created_at_begin,
            "p6": arg.created_at_end,
            "p7": arg.by_queue,
            "p8": arg.queue,
            "p9": arg.by_state,
            "p10": arg.state,
        }).first()
        if row is None:
            return None
        return models.RiverJob(
            id=row[0],
            args=row[1],
            attempt=row[2],
            attempted_at=row[3],
            attempted_by=row[4],
            created_at=row[5],
            errors=row[6],
            finalized_at=row[7],
            kind=row[8],
            max_attempts=row[9],
            metadata=row[10],
            priority=row[11],
            queue=row[12],
            state=row[13],
            scheduled_at=row[14],
            tags=row[15],
            unique_key=row[16],
        )

    def job_insert_fast(self, arg: JobInsertFastParams) -> Optional[models.RiverJob]:
        row = self._conn.execute(sqlalchemy.text(JOB_INSERT_FAST), {
            "p1": arg.args,
            "p2": arg.created_at,
            "p3": arg.finalized_at,
            "p4": arg.kind,
            "p5": arg.max_attempts,
            "p6": arg.metadata,
            "p7": arg.priority,
            "p8": arg.queue,
            "p9": arg.scheduled_at,
            "p10": arg.state,
            "p11": arg.tags,
        }).first()
        if row is None:
            return None
        return models.RiverJob(
            id=row[0],
            args=row[1],
            attempt=row[2],
            attempted_at=row[3],
            attempted_by=row[4],
            created_at=row[5],
            errors=row[6],
            finalized_at=row[7],
            kind=row[8],
            max_attempts=row[9],
            metadata=row[10],
            priority=row[11],
            queue=row[12],
            state=row[13],
            scheduled_at=row[14],
            tags=row[15],
            unique_key=row[16],
        )

    def job_insert_fast_many(self, arg: JobInsertFastManyParams) -> int:
        result = self._conn.execute(sqlalchemy.text(JOB_INSERT_FAST_MANY), {
            "p1": arg.args,
            "p2": arg.kind,
            "p3": arg.max_attempts,
            "p4": arg.metadata,
            "p5": arg.priority,
            "p6": arg.queue,
            "p7": arg.scheduled_at,
            "p8": arg.state,
            "p9": arg.tags,
        })
        return result.rowcount

    def job_insert_full(self, arg: JobInsertFullParams) -> Optional[models.RiverJob]:
        row = self._conn.execute(sqlalchemy.text(JOB_INSERT_FULL), {
            "p1": arg.args,
            "p2": arg.attempt,
            "p3": arg.attempted_at,
            "p4": arg.created_at,
            "p5": arg.errors,
            "p6": arg.finalized_at,
            "p7": arg.kind,
            "p8": arg.max_attempts,
            "p9": arg.metadata,
            "p10": arg.priority,
            "p11": arg.queue,
            "p12": arg.scheduled_at,
            "p13": arg.state,
            "p14": arg.tags,
            "p15": arg.unique_key,
        }).first()
        if row is None:
            return None
        return models.RiverJob(
            id=row[0],
            args=row[1],
            attempt=row[2],
            attempted_at=row[3],
            attempted_by=row[4],
            created_at=row[5],
            errors=row[6],
            finalized_at=row[7],
            kind=row[8],
            max_attempts=row[9],
            metadata=row[10],
            priority=row[11],
            queue=row[12],
            state=row[13],
            scheduled_at=row[14],
            tags=row[15],
            unique_key=row[16],
        )

    def job_insert_unique(self, arg: JobInsertUniqueParams) -> Optional[JobInsertUniqueRow]:
        row = self._conn.execute(sqlalchemy.text(JOB_INSERT_UNIQUE), {
            "p1": arg.args,
            "p2": arg.created_at,
            "p3": arg.finalized_at,
            "p4": arg.kind,
            "p5": arg.max_attempts,
            "p6": arg.metadata,
            "p7": arg.priority,
            "p8": arg.queue,
            "p9": arg.scheduled_at,
            "p10": arg.state,
            "p11": arg.tags,
            "p12": arg.unique_key,
        }).first()
        if row is None:
            return None
        return JobInsertUniqueRow(
            id=row[0],
            args=row[1],
            attempt=row[2],
            attempted_at=row[3],
            attempted_by=row[4],
            created_at=row[5],
            errors=row[6],
            finalized_at=row[7],
            kind=row[8],
            max_attempts=row[9],
            metadata=row[10],
            priority=row[11],
            queue=row[12],
            state=row[13],
            scheduled_at=row[14],
            tags=row[15],
            unique_key=row[16],
            unique_skipped_as_duplicate=row[17],
        )


class AsyncQuerier:
    def __init__(self, conn: sqlalchemy.ext.asyncio.AsyncConnection):
        self._conn = conn

    async def job_get_all(self) -> AsyncIterator[models.RiverJob]:
        result = await self._conn.stream(sqlalchemy.text(JOB_GET_ALL))
        async for row in result:
            yield models.RiverJob(
                id=row[0],
                args=row[1],
                attempt=row[2],
                attempted_at=row[3],
                attempted_by=row[4],
                created_at=row[5],
                errors=row[6],
                finalized_at=row[7],
                kind=row[8],
                max_attempts=row[9],
                metadata=row[10],
                priority=row[11],
                queue=row[12],
                state=row[13],
                scheduled_at=row[14],
                tags=row[15],
                unique_key=row[16],
            )

    async def job_get_by_id(self, *, id: int) -> Optional[models.RiverJob]:
        row = (await self._conn.execute(sqlalchemy.text(JOB_GET_BY_ID), {"p1": id})).first()
        if row is None:
            return None
        return models.RiverJob(
            id=row[0],
            args=row[1],
            attempt=row[2],
            attempted_at=row[3],
            attempted_by=row[4],
            created_at=row[5],
            errors=row[6],
            finalized_at=row[7],
            kind=row[8],
            max_attempts=row[9],
            metadata=row[10],
            priority=row[11],
            queue=row[12],
            state=row[13],
            scheduled_at=row[14],
            tags=row[15],
            unique_key=row[16],
        )

    async def job_get_by_kind_and_unique_properties(self, arg: JobGetByKindAndUniquePropertiesParams) -> Optional[models.RiverJob]:
        row = (await self._conn.execute(sqlalchemy.text(JOB_GET_BY_KIND_AND_UNIQUE_PROPERTIES), {
            "p1": arg.kind,
            "p2": arg.by_args,
            "p3": arg.args,
            "p4": arg.by_created_at,
            "p5": arg.created_at_begin,
            "p6": arg.created_at_end,
            "p7": arg.by_queue,
            "p8": arg.queue,
            "p9": arg.by_state,
            "p10": arg.state,
        })).first()
        if row is None:
            return None
        return models.RiverJob(
            id=row[0],
            args=row[1],
            attempt=row[2],
            attempted_at=row[3],
            attempted_by=row[4],
            created_at=row[5],
            errors=row[6],
            finalized_at=row[7],
            kind=row[8],
            max_attempts=row[9],
            metadata=row[10],
            priority=row[11],
            queue=row[12],
            state=row[13],
            scheduled_at=row[14],
            tags=row[15],
            unique_key=row[16],
        )

    async def job_insert_fast(self, arg: JobInsertFastParams) -> Optional[models.RiverJob]:
        row = (await self._conn.execute(sqlalchemy.text(JOB_INSERT_FAST), {
            "p1": arg.args,
            "p2": arg.created_at,
            "p3": arg.finalized_at,
            "p4": arg.kind,
            "p5": arg.max_attempts,
            "p6": arg.metadata,
            "p7": arg.priority,
            "p8": arg.queue,
            "p9": arg.scheduled_at,
            "p10": arg.state,
            "p11": arg.tags,
        })).first()
        if row is None:
            return None
        return models.RiverJob(
            id=row[0],
            args=row[1],
            attempt=row[2],
            attempted_at=row[3],
            attempted_by=row[4],
            created_at=row[5],
            errors=row[6],
            finalized_at=row[7],
            kind=row[8],
            max_attempts=row[9],
            metadata=row[10],
            priority=row[11],
            queue=row[12],
            state=row[13],
            scheduled_at=row[14],
            tags=row[15],
            unique_key=row[16],
        )

    async def job_insert_fast_many(self, arg: JobInsertFastManyParams) -> int:
        result = await self._conn.execute(sqlalchemy.text(JOB_INSERT_FAST_MANY), {
            "p1": arg.args,
            "p2": arg.kind,
            "p3": arg.max_attempts,
            "p4": arg.metadata,
            "p5": arg.priority,
            "p6": arg.queue,
            "p7": arg.scheduled_at,
            "p8": arg.state,
            "p9": arg.tags,
        })
        return result.rowcount

    async def job_insert_full(self, arg: JobInsertFullParams) -> Optional[models.RiverJob]:
        row = (await self._conn.execute(sqlalchemy.text(JOB_INSERT_FULL), {
            "p1": arg.args,
            "p2": arg.attempt,
            "p3": arg.attempted_at,
            "p4": arg.created_at,
            "p5": arg.errors,
            "p6": arg.finalized_at,
            "p7": arg.kind,
            "p8": arg.max_attempts,
            "p9": arg.metadata,
            "p10": arg.priority,
            "p11": arg.queue,
            "p12": arg.scheduled_at,
            "p13": arg.state,
            "p14": arg.tags,
            "p15": arg.unique_key,
        })).first()
        if row is None:
            return None
        return models.RiverJob(
            id=row[0],
            args=row[1],
            attempt=row[2],
            attempted_at=row[3],
            attempted_by=row[4],
            created_at=row[5],
            errors=row[6],
            finalized_at=row[7],
            kind=row[8],
            max_attempts=row[9],
            metadata=row[10],
            priority=row[11],
            queue=row[12],
            state=row[13],
            scheduled_at=row[14],
            tags=row[15],
            unique_key=row[16],
        )

    async def job_insert_unique(self, arg: JobInsertUniqueParams) -> Optional[JobInsertUniqueRow]:
        row = (await self._conn.execute(sqlalchemy.text(JOB_INSERT_UNIQUE), {
            "p1": arg.args,
            "p2": arg.created_at,
            "p3": arg.finalized_at,
            "p4": arg.kind,
            "p5": arg.max_attempts,
            "p6": arg.metadata,
            "p7": arg.priority,
            "p8": arg.queue,
            "p9": arg.scheduled_at,
            "p10": arg.state,
            "p11": arg.tags,
            "p12": arg.unique_key,
        })).first()
        if row is None:
            return None
        return JobInsertUniqueRow(
            id=row[0],
            args=row[1],
            attempt=row[2],
            attempted_at=row[3],
            attempted_by=row[4],
            created_at=row[5],
            errors=row[6],
            finalized_at=row[7],
            kind=row[8],
            max_attempts=row[9],
            metadata=row[10],
            priority=row[11],
            queue=row[12],
            state=row[13],
            scheduled_at=row[14],
            tags=row[15],
            unique_key=row[16],
            unique_skipped_as_duplicate=row[17],
        )
