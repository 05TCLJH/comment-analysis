"""语言检测测试。"""

from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.analysis.language import LanguageLabel, detect_language


class LanguageDetectionTest(unittest.TestCase):
    def test_detects_english_dominant_text(self) -> None:
        label = detect_language("Iran Israel war update and analysis")
        self.assertEqual(label, LanguageLabel.EN)

    def test_detects_chinese_dominant_text(self) -> None:
        label = detect_language("美以伊战争局势持续紧张，民众担忧升级")
        self.assertEqual(label, LanguageLabel.ZH)

    def test_detects_mixed_text(self) -> None:
        label = detect_language("Iran war 美以伊战争 discussion")
        self.assertEqual(label, LanguageLabel.MIXED)

    def test_empty_text_is_unknown(self) -> None:
        self.assertEqual(detect_language(""), LanguageLabel.UNKNOWN)
