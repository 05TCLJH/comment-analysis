"""清洗规则测试：验证去重、去空值、时间统一和乱码修复逻辑。"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest


# 把源码目录加入导入路径，便于直接运行测试。
ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.entry.clean import clean_records
from comment_analysis.models import CommentRecord
from comment_analysis.utils.text import clean_text


class CleanRulesTest(unittest.TestCase):
    def test_clean_text_repairs_mojibake_and_invalid_characters(self) -> None:
        mojibake_text = "\u00e4\u00bd\u00a0\u00e5\u00a5\u00bd\u0000\u200b"

        cleaned = clean_text(mojibake_text)

        self.assertEqual(cleaned, "\u4f60\u597d")

    def test_clean_records_drops_empty_and_duplicate_records(self) -> None:
        records = [
            CommentRecord(
                platform="hackernews",
                content="  first comment  ",
                source_url="https://example.com/story-1",
                crawl_time=datetime(2026, 6, 9, 10, 0, 0),
                comment_id="comment-1",
            ),
            CommentRecord(
                platform="hackernews",
                content="first comment",
                source_url="https://example.com/story-1",
                crawl_time=datetime(2026, 6, 9, 10, 0, 0),
                comment_id="comment-1-copy",
            ),
            CommentRecord(
                platform="hackernews",
                content="\u200b\u0000",
                source_url="https://example.com/story-2",
                crawl_time=datetime(2026, 6, 9, 10, 0, 0),
                comment_id="comment-2",
            ),
        ]

        cleaned_records = clean_records(records)

        self.assertEqual(len(cleaned_records), 1)
        self.assertEqual(cleaned_records[0].content, "first comment")

    def test_clean_records_normalizes_datetime_and_recovers_publish_time(self) -> None:
        records = [
            CommentRecord(
                platform="hackernews",
                content="time check",
                source_url="https://example.com/story-3",
                crawl_time=datetime(
                    2026,
                    6,
                    9,
                    10,
                    0,
                    0,
                    123456,
                    tzinfo=timezone(timedelta(hours=8)),
                ),
                comment_id="comment-3",
                publish_time=None,
                raw_data={
                    "source_item": {
                        "created_at": "2026-06-09T09:30:00Z",
                    }
                },
            )
        ]

        cleaned_records = clean_records(records)

        self.assertEqual(len(cleaned_records), 1)
        self.assertEqual(
            cleaned_records[0].crawl_time.isoformat(),
            "2026-06-09T02:00:00+00:00",
        )
        self.assertEqual(
            cleaned_records[0].publish_time.isoformat(),
            "2026-06-09T09:30:00+00:00",
        )
