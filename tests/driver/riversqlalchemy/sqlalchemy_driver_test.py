from datetime import datetime, timezone
from typing import Iterator
from unittest.mock import patch

import pytest
import sqlalchemy
import sqlalchemy.ext.asyncio

from riverqueue import (
    Client,
    InsertManyParams,
    InsertOpts,
    JobState,
    UniqueOpts,
)
from riverqueue.driver import riversqlalchemy
from riverqueue.driver.riversqlalchemy import dbsqlc


class TestSyncClient:
    #
    # fixtures
    #

    @pytest.fixture
    @staticmethod
    def test_tx(engine) -> Iterator:
        with engine.connect() as conn_tx:
            # Force SQLAlchemy to open a transaction.
            #
            # See explanatory comment in `test_tx()` above.
            transaction = conn_tx.begin()

            try:
                # Perform any setup or initialization
                conn_tx.execute(sqlalchemy.text("SELECT 1"))
                yield conn_tx
            finally:
                # Rollback the transaction
                transaction.rollback()

    @pytest.fixture
    @staticmethod
    def client(test_tx) -> Client:
        return Client(riversqlalchemy.Driver(test_tx))

    #
    # tests; should match with tests for the async client above
    #

    def test_insert_with_only_args(self, client, simple_args):
        insert_res = client.insert(simple_args)
        assert insert_res.job

    def test_insert_tx(self, client, engine, simple_args, test_tx):
        insert_res = client.insert_tx(test_tx, simple_args)
        assert insert_res.job

        job = dbsqlc.river_job.Querier(test_tx).job_get_by_id(id=insert_res.job.id)
        assert job

        with engine.begin() as test_tx2:
            transaction = test_tx2.begin()

            job = dbsqlc.river_job.Querier(test_tx2).job_get_by_id(id=insert_res.job.id)
            assert job is None

            transaction.rollback()

    def test_insert_with_opts(self, client, simple_args):
        insert_opts = InsertOpts(queue="high_priority", unique_opts=None)
        insert_res = client.insert(simple_args, insert_opts=insert_opts)
        assert insert_res.job

    def test_insert_with_unique_opts_by_args(self, client, simple_args):
        insert_opts = InsertOpts(unique_opts=UniqueOpts(by_args=True))

        insert_res = client.insert(simple_args, insert_opts=insert_opts)
        assert insert_res.job
        assert not insert_res.unique_skipped_as_duplicated

        insert_res2 = client.insert(simple_args, insert_opts=insert_opts)
        assert insert_res2.unique_skipped_as_duplicated
        assert insert_res2.job == insert_res.job

    @patch("datetime.datetime")
    def test_insert_with_unique_opts_by_period(
        self, mock_datetime, client, simple_args
    ):
        mock_datetime.now.return_value = datetime(
            2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc
        )

        insert_opts = InsertOpts(unique_opts=UniqueOpts(by_period=900))

        insert_res = client.insert(simple_args, insert_opts=insert_opts)
        assert insert_res.job
        assert not insert_res.unique_skipped_as_duplicated

        insert_res2 = client.insert(simple_args, insert_opts=insert_opts)
        assert insert_res2.job == insert_res.job
        assert insert_res2.unique_skipped_as_duplicated

    def test_insert_with_unique_opts_by_queue(self, client, simple_args):
        insert_opts = InsertOpts(unique_opts=UniqueOpts(by_queue=True))

        insert_res = client.insert(simple_args, insert_opts=insert_opts)
        assert insert_res.job
        assert not insert_res.unique_skipped_as_duplicated

        insert_res2 = client.insert(simple_args, insert_opts=insert_opts)
        assert insert_res2.job == insert_res.job
        assert insert_res2.unique_skipped_as_duplicated

    def test_insert_with_unique_opts_by_state(self, client, simple_args):
        insert_opts = InsertOpts(
            unique_opts=UniqueOpts(by_state=[JobState.AVAILABLE, JobState.RUNNING])
        )

        insert_res = client.insert(simple_args, insert_opts=insert_opts)
        assert insert_res.job
        assert not insert_res.unique_skipped_as_duplicated

        insert_res2 = client.insert(simple_args, insert_opts=insert_opts)
        assert insert_res2.job == insert_res.job
        assert insert_res2.unique_skipped_as_duplicated

    @patch("datetime.datetime")
    def test_insert_with_unique_opts_all_fast_path(
        self, mock_datetime, client, simple_args
    ):
        mock_datetime.now.return_value = datetime(
            2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc
        )

        insert_opts = InsertOpts(
            unique_opts=UniqueOpts(by_args=True, by_period=900, by_queue=True)
        )

        insert_res = client.insert(simple_args, insert_opts=insert_opts)
        assert insert_res.job
        assert not insert_res.unique_skipped_as_duplicated

        insert_res2 = client.insert(simple_args, insert_opts=insert_opts)
        assert insert_res2.job == insert_res.job
        assert insert_res2.unique_skipped_as_duplicated

    @patch("datetime.datetime")
    def test_insert_with_unique_opts_all_slow_path(
        self, mock_datetime, client, simple_args
    ):
        mock_datetime.now.return_value = datetime(
            2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc
        )

        insert_opts = InsertOpts(
            unique_opts=UniqueOpts(
                by_args=True,
                by_period=900,
                by_queue=True,
                by_state=[
                    JobState.AVAILABLE,
                    JobState.RUNNING,
                ],  # non-default states activate slow path
            )
        )

        insert_res = client.insert(simple_args, insert_opts=insert_opts)
        assert insert_res.job
        assert not insert_res.unique_skipped_as_duplicated

        insert_res2 = client.insert(simple_args, insert_opts=insert_opts)
        assert insert_res2.job == insert_res.job
        assert insert_res2.unique_skipped_as_duplicated

    def test_insert_many_with_only_args(self, client, simple_args):
        num_inserted = client.insert_many([simple_args])
        assert num_inserted == 1

    def test_insert_many_with_insert_opts(self, client, simple_args):
        num_inserted = client.insert_many(
            [
                InsertManyParams(
                    args=simple_args,
                    insert_opts=InsertOpts(queue="high_priority", unique_opts=None),
                )
            ]
        )
        assert num_inserted == 1

    def test_insert_many_tx(self, client, simple_args, test_tx):
        num_inserted = client.insert_many_tx(test_tx, [simple_args])
        assert num_inserted == 1
