"""MediaCrawlerRunner 测试。"""

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
from comment_analysis.crawlers.bridge.runner import MediaCrawlerRunner


class MediaCrawlerRunnerTest(unittest.TestCase):
    def test_run_builds_expected_env_and_command(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            mc_home = temp_path / "MediaCrawler"
            mc_home.mkdir()
            launcher = temp_path / "run_mediacrawler.py"
            launcher.write_text("# launcher", encoding="utf-8")
            save_path = temp_path / "out" / "tieba"

            runner = MediaCrawlerRunner(
                mediacrawler_home=mc_home,
                launcher_path=launcher,
                uv_executable="uv",
                login_type="cookie",
            )

            completed = MagicMock()
            completed.returncode = 0
            completed.stdout = "ok"
            completed.stderr = ""

            with patch(
                "comment_analysis.crawlers.bridge.runner.ensure_mediacrawler_ready",
                return_value=mc_home,
            ):
                with patch(
                    "comment_analysis.crawlers.bridge.runner.subprocess.run",
                    return_value=completed,
                ) as mock_run:
                    result = runner.run(
                        platform="tieba",
                        keyword="美以伊战争",
                        save_path=save_path,
                        max_notes=10,
                        max_comments_per_note=5,
                    )

            self.assertEqual(result.returncode, 0)
            mock_run.assert_called_once()
            command = mock_run.call_args.args[0]
            self.assertEqual(command[:4], ["uv", "run", "python", str(launcher)])
            env = mock_run.call_args.kwargs["env"]
            self.assertEqual(env["MC_PLATFORM"], "tieba")
            self.assertEqual(env["MC_KEYWORDS"], "美以伊战争")
            self.assertEqual(env["MC_SAVE_DATA_PATH"], str(save_path.resolve()))
            self.assertEqual(env["MC_CRAWLER_MAX_NOTES_COUNT"], "10")
            self.assertEqual(env["MC_MAX_COMMENTS_COUNT_SINGLENOTES"], "5")

    def test_run_raises_on_nonzero_exit(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            mc_home = temp_path / "MediaCrawler"
            mc_home.mkdir()
            launcher = temp_path / "run_mediacrawler.py"
            launcher.write_text("# launcher", encoding="utf-8")

            runner = MediaCrawlerRunner(
                mediacrawler_home=mc_home,
                launcher_path=launcher,
                uv_executable="",
            )

            completed = MagicMock()
            completed.returncode = 1
            completed.stdout = ""
            completed.stderr = "login failed"

            with patch(
                "comment_analysis.crawlers.bridge.runner.ensure_mediacrawler_ready",
                return_value=mc_home,
            ):
                with patch(
                    "comment_analysis.crawlers.bridge.runner.subprocess.run",
                    return_value=completed,
                ):
                    with self.assertRaises(MediaCrawlerError):
                        runner.run(
                            platform="weibo",
                            keyword="test",
                            save_path=temp_path / "out",
                            max_notes=1,
                        )


if __name__ == "__main__":
    unittest.main()
