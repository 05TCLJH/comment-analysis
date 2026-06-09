"""总入口测试：验证最小流程可以完成采集、清洗和本地存储。"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


# 把源码目录加入导入路径，便于直接运行测试。
ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.entry.run_all import run_minimal_pipeline
from comment_analysis.models import CommentRecord


class RunAllTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_records = [
            CommentRecord(
                platform="hackernews",
                content=" test keyword comment one ",
                source_url="https://example.com/story-1",
                crawl_time=datetime(2026, 6, 9, 21, 0, 0),
                comment_id="comment-1",
            ),
            CommentRecord(
                platform="hackernews",
                content="test keyword comment one",
                source_url="https://example.com/story-1",
                crawl_time=datetime(2026, 6, 9, 21, 0, 0),
                comment_id="comment-1-duplicate",
            ),
            CommentRecord(
                platform="hackernews",
                content="test keyword comment two",
                source_url="https://example.com/story-2",
                crawl_time=datetime(2026, 6, 9, 21, 0, 0),
                comment_id="comment-2",
            ),
        ]

    def test_run_minimal_pipeline_writes_json_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with patch(
                "comment_analysis.entry.run_all.collect_records",
                return_value=self.sample_records,
            ):
                result = run_minimal_pipeline(
                    keyword="test keyword",
                    output_dir=Path(temp_dir),
                    max_records=10,
                    output_format="json",
                )

            self.assertEqual(result["raw_count"], 3)
            self.assertEqual(result["cleaned_count"], 2)
            self.assertEqual(result["output_format"], "json")

            payload = json.loads(Path(result["output_path"]).read_text(encoding="utf-8"))
            self.assertEqual(len(payload), 2)
            self.assertIn("test keyword", payload[0]["content"])

    def test_run_minimal_pipeline_writes_csv_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with patch(
                "comment_analysis.entry.run_all.collect_records",
                return_value=self.sample_records,
            ):
                result = run_minimal_pipeline(
                    keyword="test keyword",
                    output_dir=Path(temp_dir),
                    max_records=10,
                    output_format="csv",
                )

            self.assertEqual(result["output_format"], "csv")

            with Path(result["output_path"]).open("r", encoding="utf-8-sig", newline="") as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["platform"], "hackernews")
