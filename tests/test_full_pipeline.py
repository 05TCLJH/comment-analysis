"""FullPipeline 集成测试（mock 采集）。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from sqlalchemy import select


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.models import CommentRecord
from comment_analysis.pipeline.orchestrator import FullPipeline
from comment_analysis.storage.sqlite import CrawlJobRow, SqliteCommentRepository


class FullPipelineTest(unittest.TestCase):
    def test_run_executes_all_stages(self) -> None:
        fake_record = CommentRecord(
            platform="hackernews",
            content="Iran Israel war",
            source_url="https://example.com/1",
            crawl_time=datetime(2026, 6, 11, 10, 0, 0),
            comment_id="hn-1",
        )
        fake_bundles = [
            {
                "platform": "hackernews",
                "raw_payload": {"hits": []},
                "records": [fake_record],
            }
        ]

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pipeline = FullPipeline(
                keyword="test",
                max_records=5,
                source="hackernews",
                database_url=f"sqlite:///{(temp_path / 'pipe.db').as_posix()}",
                raw_dir=temp_path / "raw",
                results_dir=temp_path / "results",
            )
            with patch(
                "comment_analysis.pipeline.orchestrator.collect_with_raw",
                return_value=fake_bundles,
            ):
                result = pipeline.run(top_n=5)

            self.assertTrue((temp_path / "raw" / "hackernews").exists())
            self.assertGreater(result["inserted_count"], 0)
            self.assertTrue(Path(result["report_json_path"]).exists())
            self.assertTrue(Path(result["report_html_path"]).exists())
            pipeline.close()

    def test_run_marks_job_failed_on_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_url = f"sqlite:///{(temp_path / 'fail.db').as_posix()}"
            pipeline = FullPipeline(
                keyword="test",
                max_records=5,
                source="hackernews",
                database_url=db_url,
                raw_dir=temp_path / "raw",
                results_dir=temp_path / "results",
            )
            with patch(
                "comment_analysis.pipeline.orchestrator.collect_with_raw",
                side_effect=RuntimeError("crawl failed"),
            ):
                with self.assertRaises(RuntimeError):
                    pipeline.run(top_n=5)

            repo = SqliteCommentRepository(db_url)
            with repo._Session() as session:
                status = session.execute(select(CrawlJobRow.status)).scalars().all()
            self.assertEqual(status, ["failed"])
            self.assertIsNone(repo.get_last_crawl_job_id())
            repo.close()
            pipeline.close()

    def test_rejects_non_sqlite_backend(self) -> None:
        with self.assertRaises(ValueError):
            FullPipeline(
                keyword="test",
                max_records=5,
                source="hackernews",
                storage_backend="json",
            )
