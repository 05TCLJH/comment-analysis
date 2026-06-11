"""SQLite 存储测试：去重、按 job 查询。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.models import CommentRecord, CrawlJob
from comment_analysis.storage.sqlite import SqliteCommentRepository


class SqliteRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.repo = SqliteCommentRepository(f"sqlite:///{self.db_path.as_posix()}")

    def tearDown(self) -> None:
        self.repo.close()
        self.temp_dir.cleanup()

    def _sample_record(
        self,
        comment_id: str,
        *,
        platform: str = "hackernews",
        crawl_time: datetime | None = None,
    ) -> CommentRecord:
        return CommentRecord(
            platform=platform,
            content=f"comment {comment_id}",
            source_url=f"https://example.com/{comment_id}",
            crawl_time=crawl_time or datetime(2026, 6, 11, 10, 0, 0),
            comment_id=comment_id,
        )

    def test_save_many_dedupes_by_platform_and_comment_id(self) -> None:
        job = CrawlJob(
            job_id="job-a",
            keyword="test",
            source="hackernews",
            status="running",
            started_at=datetime(2026, 6, 11, 10, 0, 0),
        )
        self.repo.create_crawl_job(job)

        first = self.repo.save_many(
            [self._sample_record("c1"), self._sample_record("c2")],
            job_id="job-a",
        )
        second = self.repo.save_many(
            [self._sample_record("c1"), self._sample_record("c3")],
            job_id="job-a",
        )

        self.assertEqual(first, 2)
        self.assertEqual(second, 1)

        rows = self.repo.fetch_comments(job_id="job-a")
        self.assertEqual(len(rows), 3)

    def test_save_many_links_existing_comments_to_new_job(self) -> None:
        self.repo.save_many(
            [self._sample_record("c1"), self._sample_record("c2")],
            job_id="job-a",
        )
        inserted = self.repo.save_many(
            [self._sample_record("c1"), self._sample_record("c3")],
            job_id="job-b",
        )

        self.assertEqual(inserted, 1)
        self.assertEqual(len(self.repo.fetch_comments(job_id="job-b")), 2)
        self.assertEqual(len(self.repo.fetch_comments(job_id="job-a")), 2)
        self.assertEqual(len(self.repo.fetch_comments()), 3)

    def test_fetch_comments_without_job_returns_all(self) -> None:
        self.repo.save_many([self._sample_record("x1")], job_id="job-x")
        self.repo.save_many([self._sample_record("x2")], job_id="job-y")
        self.assertEqual(len(self.repo.fetch_comments()), 2)

    def test_fetch_comments_filters_by_platform_and_time(self) -> None:
        self.repo.save_many(
            [
                self._sample_record(
                    "early",
                    platform="hackernews",
                    crawl_time=datetime(2026, 6, 10, 8, 0, 0),
                ),
                self._sample_record(
                    "late",
                    platform="stackexchange",
                    crawl_time=datetime(2026, 6, 11, 12, 0, 0),
                ),
            ],
            job_id="job-filter",
        )

        hn_rows = self.repo.fetch_comments(platform="hackernews")
        self.assertEqual(len(hn_rows), 1)
        self.assertEqual(hn_rows[0].comment_id, "early")

        ranged = self.repo.fetch_comments(
            since=datetime(2026, 6, 11, 0, 0, 0),
            until=datetime(2026, 6, 11, 23, 59, 59),
        )
        self.assertEqual(len(ranged), 1)
        self.assertEqual(ranged[0].comment_id, "late")

    def test_get_last_crawl_job_id_returns_latest_completed(self) -> None:
        self.repo.create_crawl_job(
            CrawlJob(
                job_id="job-running",
                keyword="k",
                source="all",
                status="running",
                started_at=datetime(2026, 6, 11, 12, 0, 0),
            )
        )
        self.repo.create_crawl_job(
            CrawlJob(
                job_id="job-1",
                keyword="k",
                source="all",
                status="completed",
                started_at=datetime(2026, 6, 11, 10, 0, 0),
                finished_at=datetime(2026, 6, 11, 10, 1, 0),
            )
        )
        self.repo.create_crawl_job(
            CrawlJob(
                job_id="job-2",
                keyword="k",
                source="all",
                status="completed",
                started_at=datetime(2026, 6, 11, 11, 0, 0),
                finished_at=datetime(2026, 6, 11, 11, 1, 0),
            )
        )
        self.assertEqual(self.repo.get_last_crawl_job_id(), "job-2")
