"""build_repository 工厂测试。"""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.storage import build_repository
from comment_analysis.storage.repository import JsonFileRepository
from comment_analysis.storage.sqlite import SqliteCommentRepository


class BuildRepositoryTest(unittest.TestCase):
    def test_default_backend_is_sqlite(self) -> None:
        with TemporaryDirectory() as temp_dir:
            db_url = f"sqlite:///{Path(temp_dir, 't.db').as_posix()}"
            repo = build_repository(backend="sqlite", database_url=db_url)
            self.assertIsInstance(repo, SqliteCommentRepository)
            repo.close()

    def test_json_backend(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "out.json"
            repo = build_repository(backend="json", output_path=path)
            self.assertIsInstance(repo, JsonFileRepository)
