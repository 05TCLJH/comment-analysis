"""分析报告语言分布测试。"""

from __future__ import annotations

import sys
from datetime import datetime
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
        self.assertEqual(report.get("analysis_engine"), "bilingual-rules-v1")


if __name__ == "__main__":
    unittest.main()
