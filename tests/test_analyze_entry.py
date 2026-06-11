"""分析入口测试：验证可以读取本地文件并输出关键词统计结果。"""

from __future__ import annotations

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

from comment_analysis.entry.analyze import run_keyword_analysis
from comment_analysis.models import CommentRecord
from comment_analysis.storage import CsvFileRepository, JsonFileRepository


class AnalyzeEntryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.records = [
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

    def test_run_keyword_analysis_reads_json_and_writes_report(self) -> None:
        with TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "comments.json"
            output_dir = Path(temp_dir) / "results"
            JsonFileRepository(input_path).save_many(self.records)

            result = run_keyword_analysis(input_path=input_path, output_dir=output_dir, top_n=3)

            report = json.loads(Path(result["output_path"]).read_text(encoding="utf-8"))
            self.assertEqual(report["total_records"], 2)
            self.assertEqual(report["top_keywords"][0]["keyword"], "iran")
            self.assertTrue(Path(result["report_path"]).exists())

            html_report = Path(result["report_path"]).read_text(encoding="utf-8")
            self.assertIn("评论分析结果报告", html_report)
            self.assertIn("时间趋势", html_report)
            self.assertIn("语言分布", html_report)
            # 语言图从 currentRecords 聚合，而非静态 RAW_DATA.language_distribution
            self.assertIn("languageData[lang]", html_report)
            self.assertIn("r.detected_language || 'unknown'", html_report)
            self.assertNotIn("RAW_DATA.language_distribution", html_report)

    def test_run_keyword_analysis_reads_csv_and_writes_report(self) -> None:
        with TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "comments.csv"
            output_dir = Path(temp_dir) / "results"
            CsvFileRepository(input_path).save_many(self.records)

            result = run_keyword_analysis(input_path=input_path, output_dir=output_dir, top_n=3)

            report = json.loads(Path(result["output_path"]).read_text(encoding="utf-8"))
            self.assertEqual(report["total_records"], 2)
            self.assertEqual(report["top_keywords"][0]["keyword"], "iran")
            self.assertTrue(Path(result["report_path"]).exists())

            html_report = Path(result["report_path"]).read_text(encoding="utf-8")
            self.assertIn("语言分布", html_report)
            self.assertIn("languageData[lang]", html_report)
