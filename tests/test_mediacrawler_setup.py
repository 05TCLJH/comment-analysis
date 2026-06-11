"""MediaCrawler 子模块 setup 测试。"""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.crawlers.bridge.exceptions import MediaCrawlerError
from comment_analysis.crawlers.bridge.setup import (
    ensure_mediacrawler_deps,
    ensure_mediacrawler_ready,
    is_submodule_initialized,
)


class MediaCrawlerSetupTest(unittest.TestCase):
    def test_is_submodule_initialized_requires_main_py(self) -> None:
        with TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            self.assertFalse(is_submodule_initialized(home))
            (home / "main.py").write_text("# mc", encoding="utf-8")
            self.assertTrue(is_submodule_initialized(home))

    def test_ensure_ready_raises_on_empty_submodule(self) -> None:
        with TemporaryDirectory() as temp_dir:
            home = Path(temp_dir) / "vendor" / "MediaCrawler"
            home.mkdir(parents=True)
            with self.assertRaises(MediaCrawlerError) as ctx:
                ensure_mediacrawler_ready(home, uv_executable="uv")
            self.assertIn("submodule update", ctx.exception.args[0].lower())

    def test_ensure_deps_runs_uv_sync_when_marker_missing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            home = Path(temp_dir) / "mc"
            home.mkdir()
            (home / "main.py").write_text("# mc", encoding="utf-8")
            (home / "pyproject.toml").write_text("[project]\nname='mc'\n", encoding="utf-8")

            marker = Path(temp_dir) / "marker"
            completed = MagicMock(returncode=0, stdout="", stderr="")

            with patch(
                "comment_analysis.crawlers.bridge.setup.DEPS_MARKER",
                marker,
            ):
                with patch(
                    "comment_analysis.crawlers.bridge.setup.subprocess.run",
                    return_value=completed,
                ) as mock_run:
                    ensure_mediacrawler_deps(home, "uv")

            mock_run.assert_called_once()
            self.assertEqual(mock_run.call_args.args[0], ["uv", "sync"])
            self.assertTrue(marker.is_file())

    def test_ensure_deps_skips_when_marker_fresh(self) -> None:
        with TemporaryDirectory() as temp_dir:
            home = Path(temp_dir) / "mc"
            home.mkdir()
            (home / "main.py").write_text("# mc", encoding="utf-8")
            (home / "pyproject.toml").write_text("[project]\nname='mc'\n", encoding="utf-8")

            marker = Path(temp_dir) / "marker"
            marker.touch()

            with patch(
                "comment_analysis.crawlers.bridge.setup.DEPS_MARKER",
                marker,
            ):
                with patch(
                    "comment_analysis.crawlers.bridge.setup.subprocess.run",
                ) as mock_run:
                    ensure_mediacrawler_deps(home, "uv")

            mock_run.assert_not_called()

    def test_ensure_ready_with_custom_home(self) -> None:
        with TemporaryDirectory() as temp_dir:
            home = Path(temp_dir) / "external"
            home.mkdir()
            (home / "main.py").write_text("# mc", encoding="utf-8")

            marker = Path(temp_dir) / "marker"
            completed = MagicMock(returncode=0, stdout="", stderr="")

            with patch(
                "comment_analysis.crawlers.bridge.setup.DEPS_MARKER",
                marker,
            ):
                with patch(
                    "comment_analysis.crawlers.bridge.setup.subprocess.run",
                    return_value=completed,
                ):
                    resolved = ensure_mediacrawler_ready(home, "uv")

            self.assertEqual(resolved, home.resolve())


if __name__ == "__main__":
    unittest.main()
