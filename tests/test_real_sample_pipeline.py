"""真实样本回归测试：覆盖抓取、清洗和分析整条链路。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

from comment_analysis.crawlers.sources import HackerNewsCommentCrawler
from comment_analysis.entry.analyze import run_keyword_analysis
from comment_analysis.entry.clean import clean_records
from comment_analysis.storage import JsonFileRepository


class RealSamplePipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = json.loads(
            (FIXTURE_DIR / "hackernews_sample_payload.json").read_text(encoding="utf-8")
        )

    def test_crawler_can_parse_real_sample_payload(self) -> None:
        crawler = HackerNewsCommentCrawler(
            keyword="缇庝互浼婃垬浜?",
            search_query="Iran Israel war",
            max_records=10,
        )

        with patch.object(crawler, "_fetch_payload", return_value=self.payload):
            records = crawler.crawl()

        self.assertEqual(len(records), 3)
        self.assertEqual(records[0].platform, "hackernews")
        self.assertEqual(records[0].source_url, "https://www.cbc.ca/news/canada/facebook-overseas-alberta-separtism-9.7223966")
        self.assertIn("Israel", records[0].content)
        self.assertEqual(records[1].publish_time.isoformat(), "2026-06-09T07:33:28+00:00")

    def test_clean_and_analyze_real_sample_records(self) -> None:
        crawler = HackerNewsCommentCrawler(
            keyword="缇庝互浼婃垬浜?",
            search_query="Iran Israel war",
            max_records=10,
        )

        with patch.object(crawler, "_fetch_payload", return_value=self.payload):
            records = crawler.crawl()

        cleaned_records = clean_records(records)

        self.assertEqual(len(cleaned_records), 3)
        self.assertEqual(cleaned_records[0].crawl_time.microsecond, 0)
        self.assertEqual(
            cleaned_records[2].publish_time.isoformat(),
            "2026-06-08T22:48:06+00:00",
        )

        with TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            input_path = temp_dir_path / "sample_comments.json"
            JsonFileRepository(input_path).save_many(cleaned_records)

            result = run_keyword_analysis(
                input_path=input_path,
                output_dir=temp_dir_path / "results",
                top_n=5,
                per_record_top_n=3,
            )

            report = json.loads(Path(result["output_path"]).read_text(encoding="utf-8"))
            html_report = Path(result["report_path"]).read_text(encoding="utf-8")

            self.assertEqual(report["total_records"], 3)
            self.assertGreater(result["unique_keywords"], 0)
            self.assertEqual(result["platform_distribution"], [{"label": "hackernews", "count": 3}])
            self.assertEqual(len(result["daily_trend"]), 2)
            self.assertTrue(Path(result["report_path"]).exists())
            self.assertIn("评论分析结果报告", html_report)
            self.assertIn("时间趋势", html_report)


if __name__ == "__main__":
    unittest.main()
