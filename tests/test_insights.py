"""规则化洞察生成测试。"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.analysis.insights import (
    build_sentiment_score_summary,
    build_word_cloud,
    generate_insights,
)
from comment_analysis.models import CommentRecord


def _record(
    *,
    platform: str = "weibo",
    content: str = "测试评论",
    sentiment_label: str = "中性",
    sentiment_score: int | None = 0,
    like_count: int | None = None,
    crawl_time: datetime | None = None,
    publish_time: datetime | None = None,
    keywords: list[str] | None = None,
) -> CommentRecord:
    raw_data: dict = {}
    if sentiment_score is not None:
        raw_data["sentiment_score"] = sentiment_score
    return CommentRecord(
        platform=platform,
        content=content,
        source_url="https://example.com/1",
        crawl_time=crawl_time or datetime(2026, 6, 11, 10, 0, 0),
        publish_time=publish_time,
        like_count=like_count,
        sentiment_label=sentiment_label,
        keywords=keywords or [],
        raw_data=raw_data,
    )


class InsightsGenerationTest(unittest.TestCase):
    def test_generate_insights_includes_platform_rule(self) -> None:
        records = [
            _record(platform="weibo", sentiment_label="消极", content=f"消极评论{i}")
            for i in range(6)
        ] + [
            _record(platform="zhihu", sentiment_label="积极", content=f"积极评论{i}")
            for i in range(6)
        ]
        platform_breakdown = [
            {
                "platform": "weibo",
                "total": 6,
                "breakdown": [
                    {"label": "消极", "count": 5},
                    {"label": "中性", "count": 1},
                ],
            },
            {
                "platform": "zhihu",
                "total": 6,
                "breakdown": [
                    {"label": "积极", "count": 5},
                    {"label": "中性", "count": 1},
                ],
            },
        ]
        insights = generate_insights(
            records,
            top_keywords=[{"keyword": "战争", "count": 3}],
            keyword_sentiment_breakdown=[
                {
                    "keyword": "战争",
                    "total": 3,
                    "sentiments": [{"label": "消极", "count": 2}, {"label": "中性", "count": 1}],
                    "platforms": [],
                }
            ],
            platform_sentiment_breakdown=platform_breakdown,
        )
        platform_insights = [item for item in insights if item["kind"] == "platform"]
        self.assertEqual(len(platform_insights), 1)
        self.assertIn("weibo", platform_insights[0]["title"])

    def test_generate_insights_includes_keyword_rule(self) -> None:
        records = [_record(content="战争局势分析")]
        insights = generate_insights(
            records,
            top_keywords=[{"keyword": "战争", "count": 5}],
            keyword_sentiment_breakdown=[
                {
                    "keyword": "战争",
                    "total": 5,
                    "sentiments": [{"label": "消极", "count": 4}, {"label": "中性", "count": 1}],
                    "platforms": [],
                }
            ],
            platform_sentiment_breakdown=[],
        )
        keyword_insights = [item for item in insights if item["kind"] == "keyword"]
        self.assertEqual(len(keyword_insights), 1)
        self.assertIn("战争", keyword_insights[0]["title"])
        self.assertIn("消极", keyword_insights[0]["body"])

    def test_generate_insights_includes_trend_rule(self) -> None:
        base = datetime(2026, 6, 11, 10, 0, 0)
        records = [
            _record(
                content=f"旧评论{i}",
                publish_time=base - timedelta(days=10 + i),
            )
            for i in range(3)
        ] + [
            _record(
                content=f"新评论{i}",
                publish_time=base - timedelta(days=i),
            )
            for i in range(5)
        ]
        insights = generate_insights(
            records,
            top_keywords=[],
            keyword_sentiment_breakdown=[],
            platform_sentiment_breakdown=[],
        )
        trend_insights = [item for item in insights if item["kind"] == "trend"]
        self.assertEqual(len(trend_insights), 1)
        self.assertIn("7 日", trend_insights[0]["title"])

    def test_generate_insights_includes_engagement_rule(self) -> None:
        records = [
            _record(content=f"普通{i}", like_count=i, sentiment_label="积极")
            for i in range(10)
        ] + [
            _record(content=f"高赞消极{i}", like_count=100 + i, sentiment_label="消极")
            for i in range(3)
        ]
        insights = generate_insights(
            records,
            top_keywords=[],
            keyword_sentiment_breakdown=[],
            platform_sentiment_breakdown=[],
        )
        engagement_insights = [item for item in insights if item["kind"] == "engagement"]
        self.assertEqual(len(engagement_insights), 1)
        self.assertIn("高互动", engagement_insights[0]["title"])

    def test_generate_insights_sorted_by_priority(self) -> None:
        base = datetime(2026, 6, 11, 10, 0, 0)
        records = [
            _record(
                platform="weibo",
                sentiment_label="消极",
                content=f"消极{i}",
                like_count=50,
                publish_time=base - timedelta(days=i),
            )
            for i in range(6)
        ]
        platform_breakdown = [
            {
                "platform": "weibo",
                "total": 6,
                "breakdown": [{"label": "消极", "count": 6}],
            }
        ]
        insights = generate_insights(
            records,
            top_keywords=[{"keyword": "战争", "count": 6}],
            keyword_sentiment_breakdown=[
                {
                    "keyword": "战争",
                    "total": 6,
                    "sentiments": [{"label": "消极", "count": 6}],
                    "platforms": [],
                }
            ],
            platform_sentiment_breakdown=platform_breakdown,
        )
        self.assertGreaterEqual(len(insights), 3)
        priorities = [item["priority"] for item in insights]
        self.assertEqual(priorities, sorted(priorities))


class WordCloudTest(unittest.TestCase):
    def test_build_word_cloud_dominant_sentiment(self) -> None:
        word_cloud = build_word_cloud(
            [{"keyword": "和平", "count": 10}, {"keyword": "战争", "count": 8}],
            [
                {
                    "keyword": "和平",
                    "total": 10,
                    "sentiments": [{"label": "积极", "count": 8}, {"label": "中性", "count": 2}],
                    "platforms": [],
                },
                {
                    "keyword": "战争",
                    "total": 8,
                    "sentiments": [{"label": "消极", "count": 7}, {"label": "中性", "count": 1}],
                    "platforms": [],
                },
            ],
        )
        self.assertEqual(len(word_cloud), 2)
        self.assertEqual(word_cloud[0]["name"], "和平")
        self.assertEqual(word_cloud[0]["dominant_sentiment"], "积极")
        self.assertEqual(word_cloud[1]["dominant_sentiment"], "消极")


class SentimentScoreSummaryTest(unittest.TestCase):
    def test_build_sentiment_score_summary(self) -> None:
        records = [
            _record(platform="weibo", sentiment_score=-4),
            _record(platform="weibo", sentiment_score=2),
            _record(platform="zhihu", sentiment_score=6),
        ]
        summary = build_sentiment_score_summary(records)
        self.assertEqual(summary["min"], -4)
        self.assertEqual(summary["max"], 6)
        self.assertIsNotNone(summary["avg"])
        self.assertEqual(len(summary["histogram"]), 10)
        self.assertEqual(len(summary["by_platform"]), 2)
        weibo_stats = next(item for item in summary["by_platform"] if item["platform"] == "weibo")
        self.assertEqual(weibo_stats["count"], 2)

    def test_build_sentiment_score_summary_empty(self) -> None:
        summary = build_sentiment_score_summary([_record(sentiment_score=None)])
        self.assertIsNone(summary["min"])
        self.assertEqual(summary["histogram"], [])


if __name__ == "__main__":
    unittest.main()
