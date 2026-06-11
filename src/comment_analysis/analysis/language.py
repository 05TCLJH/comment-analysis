"""轻量语言检测：CJK 占比 + 拉丁字母，无大模型。"""

from __future__ import annotations

from enum import Enum
import re

_CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]")
_LATIN_PATTERN = re.compile(r"[A-Za-z]")
_CJK_RATIO_THRESHOLD = 0.15
_MIN_CJK_CHARS = 2


class LanguageLabel(str, Enum):
    ZH = "zh"
    EN = "en"
    MIXED = "mixed"
    UNKNOWN = "unknown"


def detect_language(text: str) -> LanguageLabel:
    stripped = text.strip()
    if not stripped:
        return LanguageLabel.UNKNOWN

    cjk_chars = _CJK_PATTERN.findall(stripped)
    latin_chars = _LATIN_PATTERN.findall(stripped)
    meaningful_len = len(re.sub(r"\s+", "", stripped))
    if meaningful_len == 0:
        return LanguageLabel.UNKNOWN

    cjk_count = len(cjk_chars)
    cjk_ratio = cjk_count / meaningful_len
    has_cjk = cjk_count >= _MIN_CJK_CHARS and cjk_ratio >= _CJK_RATIO_THRESHOLD
    has_latin = len(latin_chars) >= 2

    if has_cjk and has_latin:
        return LanguageLabel.MIXED
    if has_cjk:
        return LanguageLabel.ZH
    if has_latin:
        return LanguageLabel.EN
    return LanguageLabel.UNKNOWN
