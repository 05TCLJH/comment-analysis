"""本地存储测试：验证 JSON 和 CSV 两种格式都能正确落地。"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


# 把源码目录加入导入路径，便于直接运行测试。
ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.models import CommentRecord
from comment_analysis.storage import CsvFileRepository, JsonFileRepository


class LocalStorageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.records = [
            CommentRecord(
                platform="hackernews",
                content="test comment one",
                source_url="https://example.com/story-1",
                crawl_time=datetime(2026, 6, 9, 21, 0, 0),
                comment_id="comment-1",
            ),
            CommentRecord(
                platform="hackernews",
                content="test comment two",
                source_url="https://example.com/story-2",
                crawl_time=datetime(2026, 6, 9, 21, 5, 0),
                comment_id="comment-2",
            ),
        ]

    def test_json_repository_writes_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "comments.json"
            repository = JsonFileRepository(output_path)

            repository.save_many(self.records)

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(len(payload), 2)
            self.assertEqual(payload[0]["content"], "test comment one")

    def test_csv_repository_writes_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "comments.csv"
            repository = CsvFileRepository(output_path)

            repository.save_many(self.records)

            with output_path.open("r", encoding="utf-8-sig", newline="") as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["content"], "test comment one")
            self.assertEqual(rows[1]["comment_id"], "comment-2")
