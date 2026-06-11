"""中文分词：jieba + 项目停用词表。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re

import jieba

_DATA_DIR = Path(__file__).resolve().parent / "data"
_STOPWORDS_PATH = _DATA_DIR / "stopwords_cn.txt"
_MIN_TOKEN_LEN = 2
_PUNCT_PATTERN = re.compile(r"^[\u3000-\u303f\uff00-\uffef\W_]+$")


@lru_cache(maxsize=1)
def _load_stopwords() -> frozenset[str]:
    if not _STOPWORDS_PATH.exists():
        return frozenset()
    lines = _STOPWORDS_PATH.read_text(encoding="utf-8").splitlines()
    return frozenset(line.strip() for line in lines if line.strip())


def tokenize_chinese(text: str) -> list[str]:
    stopwords = _load_stopwords()
    tokens: list[str] = []
    for raw in jieba.cut(text):
        token = raw.strip()
        if len(token) < _MIN_TOKEN_LEN:
            continue
        if _PUNCT_PATTERN.match(token):
            continue
        if token in stopwords:
            continue
        tokens.append(token)
    return tokens
