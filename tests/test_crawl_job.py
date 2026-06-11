"""CrawlJob 模型测试。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.models import CrawlJob


class CrawlJobTest(unittest.TestCase):
    def test_from_dict_round_trip(self) -> None:
        job = CrawlJob(
            job_id="job-001",
            keyword="美以伊战争",
            source="all",
            status="completed",
            started_at=datetime(2026, 6, 11, 10, 0, 0),
            finished_at=datetime(2026, 6, 11, 10, 1, 0),
            raw_count=10,
            cleaned_count=8,
        )
        restored = CrawlJob.from_dict(job.to_dict())
        self.assertEqual(restored.job_id, "job-001")
        self.assertEqual(restored.cleaned_count, 8)
