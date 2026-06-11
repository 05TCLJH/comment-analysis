"""中文 jieba 分词测试。"""

from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.analysis.tokenize_cn import tokenize_chinese


class TokenizeChineseTest(unittest.TestCase):
    def test_tokenize_chinese_extracts_meaningful_terms(self) -> None:
        tokens = tokenize_chinese("美以伊战争局势紧张，民众担忧冲突升级")
        self.assertIn("战争", tokens)
        self.assertIn("冲突", tokens)
        self.assertNotIn("的", tokens)
        self.assertNotIn("，", tokens)

    def test_tokenize_chinese_filters_stopwords(self) -> None:
        tokens = tokenize_chinese("这是一个测试")
        self.assertNotIn("一个", tokens)
