"""analyze --from-db 测试。"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.entry.analyze import run_analysis_from_db
from comment_analysis.models import CommentRecord, CrawlJob
from comment_analysis.storage.sqlite import SqliteCommentRepository


class AnalyzeFromDbTest(unittest.TestCase):
    def test_run_analysis_from_db_by_job_id(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_url = f"sqlite:///{(temp_path / 'a.db').as_posix()}"
            repo = SqliteCommentRepository(db_url)
            job_id = "job-analyze-1"
            repo.create_crawl_job(
                CrawlJob(
                    job_id=job_id,
                    keyword="test",
                    source="hackernews",
                    status="completed",
                    started_at=datetime(2026, 6, 11, 10, 0, 0),
                    finished_at=datetime(2026, 6, 11, 10, 1, 0),
                )
            )
            repo.save_many(
                [
                    CommentRecord(
                        platform="hackernews",
                        content="Iran Israel war update",
                        source_url="https://example.com/1",
                        crawl_time=datetime(2026, 6, 11, 10, 0, 0),
                        comment_id="c1",
                    )
                ],
                job_id=job_id,
            )

            result = run_analysis_from_db(
                database_url=db_url,
                job_id=job_id,
                output_dir=temp_path / "results",
                top_n=5,
            )
            report = json.loads(Path(result["output_path"]).read_text(encoding="utf-8"))
            self.assertEqual(report["total_records"], 1)
            self.assertTrue(Path(result["report_path"]).exists())
            repo.close()

    def test_run_analysis_from_db_last_job(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_url = f"sqlite:///{(temp_path / 'b.db').as_posix()}"
            repo = SqliteCommentRepository(db_url)

            repo.create_crawl_job(
                CrawlJob(
                    job_id="job-old",
                    keyword="test",
                    source="hackernews",
                    status="completed",
                    started_at=datetime(2026, 6, 11, 9, 0, 0),
                    finished_at=datetime(2026, 6, 11, 9, 1, 0),
                )
            )
            repo.create_crawl_job(
                CrawlJob(
                    job_id="job-latest",
                    keyword="test",
                    source="hackernews",
                    status="completed",
                    started_at=datetime(2026, 6, 11, 10, 0, 0),
                    finished_at=datetime(2026, 6, 11, 10, 1, 0),
                )
            )
            repo.save_many(
                [
                    CommentRecord(
                        platform="hackernews",
                        content="Iran war latest",
                        source_url="https://example.com/2",
                        crawl_time=datetime(2026, 6, 11, 10, 0, 0),
                        comment_id="c-latest",
                    )
                ],
                job_id="job-latest",
            )

            result = run_analysis_from_db(
                database_url=db_url,
                last_job=True,
                output_dir=temp_path / "results",
                top_n=5,
            )
            self.assertEqual(result["job_id"], "job-latest")
            report = json.loads(Path(result["output_path"]).read_text(encoding="utf-8"))
            self.assertEqual(report["total_records"], 1)
            repo.close()

    def test_run_analysis_from_db_last_job_includes_linked_duplicates(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_url = f"sqlite:///{(temp_path / 'c.db').as_posix()}"
            repo = SqliteCommentRepository(db_url)

            repo.create_crawl_job(
                CrawlJob(
                    job_id="job-first",
                    keyword="test",
                    source="hackernews",
                    status="completed",
                    started_at=datetime(2026, 6, 11, 9, 0, 0),
                    finished_at=datetime(2026, 6, 11, 9, 1, 0),
                )
            )
            repo.create_crawl_job(
                CrawlJob(
                    job_id="job-second",
                    keyword="test",
                    source="hackernews",
                    status="completed",
                    started_at=datetime(2026, 6, 11, 10, 0, 0),
                    finished_at=datetime(2026, 6, 11, 10, 1, 0),
                )
            )
            shared = CommentRecord(
                platform="hackernews",
                content="Iran Israel war update",
                source_url="https://example.com/shared",
                crawl_time=datetime(2026, 6, 11, 10, 0, 0),
                comment_id="shared-1",
            )
            repo.save_many([shared], job_id="job-first")
            repo.save_many([shared], job_id="job-second")

            result = run_analysis_from_db(
                database_url=db_url,
                job_id="job-second",
                output_dir=temp_path / "results",
                top_n=5,
            )
            report = json.loads(Path(result["output_path"]).read_text(encoding="utf-8"))
            self.assertEqual(report["total_records"], 1)
            repo.close()

    def test_run_analysis_from_db_raises_when_no_completed_job(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_url = f"sqlite:///{(temp_path / 'd.db').as_posix()}"
            repo = SqliteCommentRepository(db_url)
            repo.create_crawl_job(
                CrawlJob(
                    job_id="job-running",
                    keyword="test",
                    source="hackernews",
                    status="running",
                    started_at=datetime(2026, 6, 11, 10, 0, 0),
                )
            )
            repo.close()

            with self.assertRaises(ValueError):
                run_analysis_from_db(database_url=db_url, last_job=True)
