"""评论数据模型测试：验证标准化和字典转换逻辑。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
import unittest


# 把源码目录加入导入路径，便于直接运行测试。
ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.models import CommentRecord


class CommentRecordTest(unittest.TestCase):
    def test_to_dict_serializes_datetime_and_normalizes_fields(self) -> None:
        record = CommentRecord(
            platform="  weibo  ",
            content="  Hello world  ",
            source_url=" https://example.com/post/1 ",
            crawl_time=datetime(2026, 6, 9, 12, 30, 0),
            title="  A post title  ",
            author="  Alice  ",
            author_id="  12345  ",
            comment_id="  c-1  ",
            publish_time="2026-06-08T10:00:00",
            like_count="12",
            reply_count=3.0,
            sentiment_label=" 正向 ",
            keywords=[" 战争 ", "分析", "战争"],
            raw_data={"source": "raw"},
        )

        payload = record.to_dict()

        self.assertEqual(payload["platform"], "weibo")
        self.assertEqual(payload["content"], "Hello world")
        self.assertEqual(payload["source_url"], "https://example.com/post/1")
        self.assertEqual(payload["crawl_time"], "2026-06-09T12:30:00")
        self.assertEqual(payload["publish_time"], "2026-06-08T10:00:00")
        self.assertEqual(payload["like_count"], 12)
        self.assertEqual(payload["reply_count"], 3)
        self.assertEqual(payload["keywords"], ["战争", "分析"])
        self.assertEqual(payload["raw_data"], {"source": "raw"})

    def test_from_dict_builds_record(self) -> None:
        record = CommentRecord.from_dict(
            {
                "platform": "x",
                "content": "comment",
                "source_url": "https://example.com",
                "crawl_time": "2026-06-09T12:30:00",
                "keywords": ("alpha", "beta"),
                "like_count": "5",
            }
        )

        self.assertEqual(record.platform, "x")
        self.assertEqual(record.like_count, 5)
        self.assertEqual(record.keywords, ["alpha", "beta"])
        self.assertEqual(record.to_dict()["crawl_time"], "2026-06-09T12:30:00")


if __name__ == "__main__":
    unittest.main()
