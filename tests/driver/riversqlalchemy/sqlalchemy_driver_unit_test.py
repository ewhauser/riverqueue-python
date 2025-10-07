from riverqueue.driver import JobInsertParams
from riverqueue.driver.riversqlalchemy import sql_alchemy_driver
from riverqueue.driver.riversqlalchemy.dbsqlc import river_job


def test_build_insert_params_aligns_unique_fields():
    non_unique = JobInsertParams(
        kind="first",
        args='{"job": "first"}',
        unique_key=None,
        unique_state=None,
    )
    unique_key = memoryview(b"second-unique")
    unique = JobInsertParams(
        kind="second",
        args='{"job": "second"}',
        unique_key=unique_key,
        unique_state=42,
    )

    params = sql_alchemy_driver._build_insert_params(
        river_job.JobInsertFastManyParams,
        [non_unique, unique],
    )

    assert params.kind == ["first", "second"]
    assert params.args == ['{"job": "first"}', '{"job": "second"}']
    assert params.unique_key == [None, unique_key]
    assert params.unique_states == [None, 42]
