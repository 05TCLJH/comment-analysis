"""解析器测试：验证原始接口数据能转换为统一评论结构。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
import unittest


# 把源码目录加入导入路径，便于直接运行测试。
ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.parsers import HackerNewsCommentParser


class HackerNewsParserTest(unittest.TestCase):
    def test_parse_builds_comment_record(self) -> None:
        parser = HackerNewsCommentParser(
            keyword="美以伊战争",
            search_query="Iran Israel war",
        )
        raw_item = {
            "hit": {
                "objectID": "1001",
                "comment_text": "<p>Hello <em>world</em></p>",
                "story_title": "Story title",
                "story_url": "https://example.com/story-1",
                "author": "alice",
                "created_at": "2026-06-09T10:00:00Z",
            },
            "crawl_time": datetime(2026, 6, 9, 12, 0, 0),
        }

        record = parser.parse(raw_item)

        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record.platform, "hackernews")
        self.assertEqual(record.content, "Hello world")
        self.assertEqual(record.title, "Story title")
        self.assertEqual(record.author, "alice")
        self.assertEqual(record.comment_id, "1001")
        self.assertEqual(record.source_url, "https://example.com/story-1")
        self.assertEqual(record.crawl_time.isoformat(), "2026-06-09T12:00:00")
        self.assertEqual(record.raw_data["search_query"], "Iran Israel war")

    def test_parse_skips_empty_comment(self) -> None:
        parser = HackerNewsCommentParser(
            keyword="美以伊战争",
            search_query="Iran Israel war",
        )
        raw_item = {
            "hit": {
                "objectID": "1002",
                "comment_text": "",
            },
            "crawl_time": datetime(2026, 6, 9, 12, 0, 0),
        }

        record = parser.parse(raw_item)

        self.assertIsNone(record)
