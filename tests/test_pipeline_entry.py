"""pipeline CLI 入口测试。"""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.entry.pipeline import run_full_pipeline


class PipelineEntryTest(unittest.TestCase):
    def test_run_full_pipeline_delegates_to_full_pipeline(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with patch("comment_analysis.entry.pipeline.FullPipeline") as mock_cls:
                instance = mock_cls.return_value
                instance.run.return_value = {
                    "job_id": "job-x",
                    "database_url": "sqlite:///x.db",
                    "report_json_path": Path(temp_dir) / "a.json",
                    "report_html_path": Path(temp_dir) / "a.html",
                    "inserted_count": 3,
                    "raw_count": 3,
                    "cleaned_count": 3,
                }
                result = run_full_pipeline(
                    keyword="test",
                    limit=5,
                    source="hackernews",
                    results_dir=Path(temp_dir),
                )
                self.assertEqual(result["job_id"], "job-x")
                instance.run.assert_called_once()
                instance.close.assert_called_once()
