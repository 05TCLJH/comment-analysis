"""Raw 落盘测试。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.storage.raw import RawFileRepository


class RawRepositoryTest(unittest.TestCase):
    def test_save_payload_writes_expected_path(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo = RawFileRepository(Path(temp_dir))
            path = repo.save_payload(
                platform="hackernews",
                job_id="job-abc",
                payload={"hits": [{"objectID": "1"}]},
            )
            self.assertEqual(path, Path(temp_dir) / "hackernews" / "job-abc.json")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["hits"][0]["objectID"], "1")
