# tests/test_nltk_data.py
"""NLTK 数据引导测试。"""

from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.analysis.nltk_data import ensure_nltk_data, NLTK_PACKAGES


class NltkDataTest(unittest.TestCase):
    def test_nltk_packages_contains_required_resources(self) -> None:
        self.assertIn("punkt_tab", NLTK_PACKAGES)
        self.assertIn("stopwords", NLTK_PACKAGES)
        self.assertIn("wordnet", NLTK_PACKAGES)

    def test_ensure_nltk_data_downloads_missing_packages(self) -> None:
        import comment_analysis.analysis.nltk_data as nltk_data_module

        nltk_data_module._downloaded = False
        with patch("comment_analysis.analysis.nltk_data.nltk.data.find", side_effect=LookupError):
            with patch("comment_analysis.analysis.nltk_data.nltk.download") as mock_download:
                ensure_nltk_data()
                self.assertEqual(mock_download.call_count, len(NLTK_PACKAGES))
