"""英文 NLTK 分词测试。"""

from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.analysis.tokenize_en import tokenize_english


class TokenizeEnglishTest(unittest.TestCase):
    @patch("comment_analysis.analysis.tokenize_en.ensure_nltk_data")
    def test_tokenize_english_lemmatizes_war_variants(self, _mock: object) -> None:
        tokens = tokenize_english("The wars in Iran and Israel are escalating")
        self.assertIn("war", tokens)
        self.assertNotIn("wars", tokens)
        self.assertIn("iran", tokens)
        self.assertNotIn("the", tokens)

    @patch("comment_analysis.analysis.tokenize_en.ensure_nltk_data")
    def test_tokenize_english_keeps_hyphenated_terms(self, _mock: object) -> None:
        tokens = tokenize_english("cross-border conflict update")
        self.assertTrue("cross" in tokens or "border" in tokens)
