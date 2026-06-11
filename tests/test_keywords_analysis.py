"""关键词分析测试：验证词项提取和高频词统计结果。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
import unittest


# 把源码目录加入导入路径，便于直接运行测试。
ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.analysis import assign_keywords, build_keyword_report, tokenize_text
from comment_analysis.analysis.language import LanguageLabel, detect_language
from comment_analysis.models import CommentRecord


class KeywordsAnalysisTest(unittest.TestCase):
    def test_tokenize_text_extracts_chinese_and_english_terms(self) -> None:
        tokens = tokenize_text("Iran Israel war 美以伊战争 update")

        self.assertIn("iran", tokens)
        self.assertIn("israel", tokens)
        self.assertIn("war", tokens)
        self.assertTrue(any("战争" in t or "美以" in t for t in tokens))
        self.assertNotIn("and", tokens)

    def test_build_keyword_report_counts_high_frequency_terms(self) -> None:
        records = [
            CommentRecord(
                platform="hackernews",
                content="Iran Israel war update",
                source_url="https://example.com/story-1",
                crawl_time=datetime(2026, 6, 9, 12, 0, 0),
            ),
            CommentRecord(
                platform="hackernews",
                content="Iran war analysis",
                source_url="https://example.com/story-2",
                crawl_time=datetime(2026, 6, 9, 12, 5, 0),
            ),
        ]

        report = build_keyword_report(records, top_n=3)

        self.assertEqual(report["total_records"], 2)
        self.assertGreaterEqual(report["unique_keywords"], 4)
        self.assertEqual(report["top_keywords"][0]["keyword"], "iran")
        self.assertEqual(report["top_keywords"][0]["count"], 2)

    def test_assign_keywords_fills_record_keywords(self) -> None:
        record = CommentRecord(
            platform="hackernews",
            content="Iran Israel war update",
            source_url="https://example.com/story-3",
            crawl_time=datetime(2026, 6, 9, 12, 10, 0),
        )

        updated_record = assign_keywords([record], top_n=3)[0]

        self.assertEqual(len(updated_record.keywords), 3)
        self.assertIn("iran", updated_record.keywords)


class BilingualKeywordsTest(unittest.TestCase):
    def test_tokenize_text_routes_mixed_text_to_both_pipelines(self) -> None:
        tokens = tokenize_text("Iran war 美以伊战争 update")
        self.assertIn("iran", tokens)
        self.assertIn("war", tokens)
        self.assertTrue(any("战争" in t or "美以" in t for t in tokens))

    def test_detect_language_used_for_routing(self) -> None:
        self.assertEqual(detect_language("Iran Israel war"), LanguageLabel.EN)
        self.assertEqual(detect_language("美以伊战争局势"), LanguageLabel.ZH)
