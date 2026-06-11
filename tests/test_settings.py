"""配置测试：验证 dotenv 加载与默认 SQLite 路径。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class SettingsTest(unittest.TestCase):
    def test_default_database_url_points_to_sqlite_file(self) -> None:
        import importlib
        import comment_analysis.config.settings as settings_module

        importlib.reload(settings_module)
        url = settings_module.settings.database_url
        self.assertTrue(url.startswith("sqlite:///"))
        self.assertIn("comment_analysis.db", url)

    def test_dotenv_overrides_database_url(self) -> None:
        import importlib
        import comment_analysis.config.settings as settings_module

        os.environ["DATABASE_URL"] = "sqlite:///tmp/test_override.db"
        try:
            importlib.reload(settings_module)
            self.assertEqual(
                settings_module.settings.database_url,
                "sqlite:///tmp/test_override.db",
            )
        finally:
            del os.environ["DATABASE_URL"]
            importlib.reload(settings_module)
