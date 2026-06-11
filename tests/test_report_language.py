"""分析报告语言分布与 v2 增强字段测试。"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.analysis import assign_keywords, assign_sentiment, build_analysis_report
from comment_analysis.models import CommentRecord


class ReportLanguageTest(unittest.TestCase):
    @patch("comment_analysis.analysis.sentiment.ensure_nltk_data")
    def test_build_analysis_report_includes_language_distribution(self, _mock: object) -> None:
        records = [
            CommentRecord(
                platform="hackernews",
                content="Iran Israel war update",
                source_url="https://example.com/1",
                crawl_time=datetime(2026, 6, 11, 10, 0, 0),
            ),
            CommentRecord(
                platform="stackexchange",
                content="美以伊战争局势分析",
                source_url="https://example.com/2",
                crawl_time=datetime(2026, 6, 11, 10, 5, 0),
            ),
        ]
        enriched = assign_sentiment(assign_keywords(records, top_n=5))
        report = build_analysis_report(enriched, top_n=10)

        self.assertIn("language_distribution", report)
        labels = {item["label"] for item in report["language_distribution"]}
        self.assertTrue({"en", "zh"} & labels or "mixed" in labels)
        self.assertIn("detected_language", report["records"][0])
        self.assertEqual(report.get("analysis_engine"), "bilingual-rules-v2")

    @patch("comment_analysis.analysis.sentiment.ensure_nltk_data")
    def test_build_analysis_report_includes_v2_fields(self, _mock: object) -> None:
        base = datetime(2026, 6, 11, 10, 0, 0)
        records = [
            CommentRecord(
                platform="weibo",
                content="战争带来危险和死亡，局势非常混乱",
                source_url=f"https://example.com/{index}",
                crawl_time=base,
                publish_time=base - timedelta(days=index),
                like_count=index * 10,
            )
            for index in range(6)
        ] + [
            CommentRecord(
                platform="zhihu",
                content="希望实现和平与安全，局势趋于稳定",
                source_url=f"https://example.com/z{index}",
                crawl_time=base,
                publish_time=base - timedelta(days=index + 10),
                like_count=index,
            )
            for index in range(6)
        ]
        enriched = assign_sentiment(assign_keywords(records, top_n=5))
        report = build_analysis_report(enriched, top_n=10)

        self.assertIn("word_cloud", report)
        self.assertIn("insights", report)
        self.assertIn("sentiment_score_summary", report)
        self.assertGreaterEqual(len(report["insights"]), 3)
        self.assertTrue(all("id" in item and "priority" in item for item in report["insights"]))

        for record in report["records"]:
            self.assertIn("sentiment_score", record)

        summary = report["sentiment_score_summary"]
        self.assertIn("histogram", summary)
        self.assertIn("by_platform", summary)
        self.assertIsNotNone(summary["avg"])

        if report["word_cloud"]:
            item = report["word_cloud"][0]
            self.assertIn(item["dominant_sentiment"], ("积极", "中性", "消极"))


if __name__ == "__main__":
    unittest.main()
