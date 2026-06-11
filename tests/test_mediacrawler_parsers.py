"""MediaCrawler JSONL 解析器测试。"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.crawlers.bridge.jsonl_reader import JsonlCommentReader
from comment_analysis.parsers import TiebaCommentParser, WeiboCommentParser, ZhihuCommentParser

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "mediacrawler"


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


class MediaCrawlerParserTest(unittest.TestCase):
    def setUp(self) -> None:
        self.crawl_time = datetime(2026, 6, 11, 10, 0, 0)

    def test_tieba_parser(self) -> None:
        content_index = {"8888": {"title": "美以伊局势讨论帖"}}
        parser = TiebaCommentParser(keyword="美以伊战争", content_index=content_index)
        rows = _load_jsonl(FIXTURES / "tieba_comments.jsonl")
        records = parser.parse_many(
            [{"item": row, "crawl_time": self.crawl_time} for row in rows]
        )
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].platform, "tieba")
        self.assertEqual(records[0].content, "这是贴吧评论内容")
        self.assertEqual(records[0].title, "美以伊局势讨论帖")
        self.assertEqual(records[0].comment_id, "1001")
        self.assertEqual(records[1].comment_id, "1002")

    def test_zhihu_parser(self) -> None:
        content_index = {
            "answer-1": {
                "title": "如何看待中东局势",
                "content_url": "https://www.zhihu.com/question/123/answer/answer-1",
                "question_id": "123",
            }
        }
        parser = ZhihuCommentParser(keyword="美以伊战争", content_index=content_index)
        rows = _load_jsonl(FIXTURES / "zhihu_comments.jsonl")
        records = parser.parse_many(
            [{"item": row, "crawl_time": self.crawl_time} for row in rows]
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].platform, "zhihu")
        self.assertIn("zhihu.com", records[0].source_url)
        self.assertEqual(records[0].like_count, 5)

    def test_weibo_parser(self) -> None:
        content_index = {"5555": {"content": "原博：局势更新"}}
        parser = WeiboCommentParser(keyword="美以伊战争", content_index=content_index)
        rows = _load_jsonl(FIXTURES / "weibo_comments.jsonl")
        records = parser.parse_many(
            [{"item": row, "crawl_time": self.crawl_time} for row in rows]
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].platform, "weibo")
        self.assertEqual(records[0].content, "微博评论 测试")
        self.assertEqual(records[0].source_url, "https://m.weibo.cn/detail/5555")

    def test_jsonl_reader(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            jsonl_dir = temp_path / "jsonl"
            jsonl_dir.mkdir(parents=True)
            shutil.copy(
                FIXTURES / "tieba_comments.jsonl",
                jsonl_dir / "search_comments_20260611.jsonl",
            )
            shutil.copy(
                FIXTURES / "tieba_contents.jsonl",
                jsonl_dir / "search_contents_20260611.jsonl",
            )
            reader = JsonlCommentReader(temp_path)
            comments = reader.read_comments()
            contents = reader.read_contents()
            index = reader.build_content_index()
            self.assertEqual(len(comments), 2)
            self.assertEqual(len(contents), 1)
            self.assertIn("8888", index)


if __name__ == "__main__":
    unittest.main()
