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
