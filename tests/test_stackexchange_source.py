"""Stack Exchange 数据源回归测试。"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

from comment_analysis.crawlers.sources import StackExchangeCommentCrawler
from comment_analysis.entry.crawl import collect_records
from comment_analysis.entry.run_all import run_minimal_pipeline
from comment_analysis.parsers import StackExchangeCommentParser


class StackExchangeSourceTest(unittest.TestCase):
    def setUp(self) -> None:
        payload = json.loads(
            (FIXTURE_DIR / "stackexchange_sample_payload.json").read_text(encoding="utf-8")
        )
        self.question_payload = payload["questions"]
        self.comments_payload = payload["comments"]
        self.question_item = self.question_payload["items"][0]
        self.comment_item = self.comments_payload["items"][0]

    def test_parser_builds_comment_record_from_real_sample(self) -> None:
        parser = StackExchangeCommentParser(
            keyword="美以伊战争",
            search_query="Iran Israel war",
            site="politics",
        )

        record = parser.parse(
            {
                "question": self.question_item,
                "comment": self.comment_item,
                "crawl_time": datetime(2026, 6, 10, 10, 30, 0),
            }
        )

        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record.platform, "stackexchange")
        self.assertEqual(record.author, "Guran")
        self.assertEqual(record.author_id, "16225")
        self.assertEqual(record.comment_id, "434227")
        self.assertIn("politics.stackexchange.com/questions/94570", record.source_url)
        self.assertIn("#comment434227_94570", record.source_url)
        self.assertIn("influenced", record.content)
        self.assertEqual(record.title, self.question_item["title"])
        self.assertEqual(record.publish_time.isoformat(), "2026-04-21T12:25:56+00:00")

    def test_collect_records_uses_stackexchange_source(self) -> None:
        def fetch_side_effect(url: str):
            if "/search/advanced" in url:
                return self.question_payload
            if "/comments" in url:
                return self.comments_payload
            raise AssertionError(f"意外的请求地址：{url}")

        with patch.object(
            StackExchangeCommentCrawler,
            "_fetch_payload",
            side_effect=fetch_side_effect,
        ):
            records = collect_records(
                keyword="美以伊战争",
                max_records=10,
                source="stackexchange",
            )

        self.assertEqual(len(records), 3)
        self.assertTrue(all(record.platform == "stackexchange" for record in records))
        self.assertEqual(records[0].author, "Guran")
        self.assertEqual(records[1].author, "AakashM")

    def test_run_minimal_pipeline_can_use_stackexchange_source(self) -> None:
        def fetch_side_effect(url: str):
            if "/search/advanced" in url:
                return self.question_payload
            if "/comments" in url:
                return self.comments_payload
            raise AssertionError(f"意外的请求地址：{url}")

        with TemporaryDirectory() as temp_dir:
            with patch.object(
                StackExchangeCommentCrawler,
                "_fetch_payload",
                side_effect=fetch_side_effect,
            ):
                result = run_minimal_pipeline(
                    keyword="美以伊战争",
                    output_dir=Path(temp_dir),
                    max_records=10,
                    output_format="json",
                    source="stackexchange",
                )

            payload = json.loads(Path(result["output_path"]).read_text(encoding="utf-8"))
            self.assertEqual(result["source"], "stackexchange")
            self.assertEqual(result["raw_count"], 3)
            self.assertEqual(result["cleaned_count"], 3)
            self.assertEqual(len(payload), 3)
            self.assertEqual(payload[0]["platform"], "stackexchange")
            self.assertEqual(payload[0]["title"], self.question_item["title"])


if __name__ == "__main__":
    unittest.main()
