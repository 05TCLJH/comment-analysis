"""双语情感分析测试。"""

from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import patch
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.analysis import assign_sentiment, classify_sentiment
from comment_analysis.models import CommentRecord


class SentimentBilingualTest(unittest.TestCase):
    @patch("comment_analysis.analysis.sentiment.ensure_nltk_data")
    def test_english_positive_vader(self, _mock: object) -> None:
        label, score = classify_sentiment("This is a wonderful peace agreement and great hope")
        self.assertEqual(label, "积极")
        self.assertGreater(score, 0)

    @patch("comment_analysis.analysis.sentiment.ensure_nltk_data")
    def test_english_negative_vader(self, _mock: object) -> None:
        label, score = classify_sentiment("Terrible war, awful attack and horrible crisis")
        self.assertEqual(label, "消极")
        self.assertLess(score, 0)

    def test_chinese_negative_dictionary(self) -> None:
        label, score = classify_sentiment("战争带来危险和死亡，局势非常混乱")
        self.assertEqual(label, "消极")
        self.assertLessEqual(score, -2)

    def test_chinese_positive_dictionary(self) -> None:
        label, score = classify_sentiment("希望实现和平与安全，局势趋于稳定")
        self.assertEqual(label, "积极")
        self.assertGreaterEqual(score, 2)

    @patch("comment_analysis.analysis.sentiment.ensure_nltk_data")
    def test_assign_sentiment_mixed_record(self, _mock: object) -> None:
        record = CommentRecord(
            platform="hackernews",
            content="Iran war 战争危险",
            source_url="https://example.com/1",
            crawl_time=datetime(2026, 6, 11, 10, 0, 0),
        )
        updated = assign_sentiment([record])[0]
        self.assertIn(updated.sentiment_label, ("积极", "中性", "消极"))
        self.assertIn("sentiment_score", updated.raw_data)
        self.assertIn("detected_language", updated.raw_data)
