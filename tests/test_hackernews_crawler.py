"""真实采集器测试：验证原始接口结果会交给解析层处理。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
import unittest
from unittest.mock import patch


# 把源码目录加入导入路径，便于直接运行测试。
ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.crawlers.sources import HackerNewsCommentCrawler


class HackerNewsCrawlerTest(unittest.TestCase):
    def test_crawl_uses_parser_to_convert_hits(self) -> None:
        crawler = HackerNewsCommentCrawler(
            keyword="美以伊战争",
            search_query="Iran Israel war",
            max_records=5,
        )

        payload = {
            "hits": [
                {
                    "objectID": "1001",
                    "comment_text": "<p>Hello <em>world</em></p>",
                    "story_title": "Story title",
                    "story_url": "https://example.com/story-1",
                    "author": "alice",
                    "created_at": "2026-06-09T10:00:00Z",
                },
                {
                    "objectID": "1002",
                    "comment_text": "",
                    "story_title": "Empty comment",
                    "author": "bob",
                    "created_at": "2026-06-09T11:00:00Z",
                },
            ]
        }

        with patch.object(crawler, "_fetch_payload", return_value=payload):
            records = crawler.crawl()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].platform, "hackernews")
        self.assertEqual(records[0].content, "Hello world")
        self.assertEqual(records[0].title, "Story title")
        self.assertEqual(records[0].author, "alice")
        self.assertEqual(records[0].comment_id, "1001")
        self.assertEqual(records[0].source_url, "https://example.com/story-1")
        self.assertEqual(records[0].raw_data["search_query"], "Iran Israel war")

    def test_crawl_wraps_hits_before_parsing(self) -> None:
        crawler = HackerNewsCommentCrawler(
            keyword="美以伊战争",
            search_query="Iran Israel war",
            max_records=5,
        )

        payload = {
            "hits": [
                {
                    "objectID": "1001",
                    "comment_text": "<p>Hello</p>",
                }
            ]
        }

        with patch.object(crawler, "_fetch_payload", return_value=payload):
            with patch.object(crawler.parser, "parse_many", return_value=[]) as parse_many:
                crawler.crawl()

        parse_items = parse_many.call_args.args[0]
        self.assertEqual(len(parse_items), 1)
        self.assertEqual(parse_items[0]["hit"]["objectID"], "1001")
        self.assertIsInstance(parse_items[0]["crawl_time"], datetime)
