"""文本工具模块：提供基础清洗、乱码修复和字符过滤能力。"""

from __future__ import annotations

from html import unescape
import unicodedata


_SUSPICIOUS_MOJIBAKE_MARKERS = (
    "\u00c3",
    "\u00c2",
    "\u00e2",
    "\u00e4",
    "\u00e5",
    "\u00e6",
    "\u00e7",
    "\u00f0",
)


def normalize_whitespace(text: str) -> str:
    """把连续空白折叠为单个空格。"""
    return " ".join(text.split())


def strip_invalid_characters(text: str) -> str:
    """移除控制字符、零宽字符等无效内容。"""
    result: list[str] = []
    for char in text:
        if char in {"\n", "\r", "\t"}:
            result.append(" ")
            continue

        category = unicodedata.category(char)
        if category.startswith("C"):
            continue

        result.append(char)

    return "".join(result)


def _looks_like_mojibake(text: str) -> bool:
    """判断文本是否像常见的编码乱码。"""
    return any(marker in text for marker in _SUSPICIOUS_MOJIBAKE_MARKERS)


def _drop_unencodable_characters(text: str, encoding: str) -> str:
    """移除无法按指定编码写出的字符，避免修复过程被脏字符打断。"""
    result: list[str] = []
    for char in text:
        try:
            char.encode(encoding)
        except UnicodeEncodeError:
            continue
        result.append(char)
    return "".join(result)


def _score_text_quality(text: str) -> int:
    """根据可读性给文本打分，用于选择更可信的修复结果。"""
    suspicious_count = sum(text.count(marker) for marker in _SUSPICIOUS_MOJIBAKE_MARKERS)
    cjk_count = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    printable_count = sum(1 for char in text if char.isprintable())
    return cjk_count * 4 + printable_count - suspicious_count * 5


def repair_mojibake(text: str) -> str:
    """尝试修复常见的 UTF-8 被错误解码后的乱码。"""
    if not text or not _looks_like_mojibake(text):
        return text

    original_suspicious_count = sum(text.count(marker) for marker in _SUSPICIOUS_MOJIBAKE_MARKERS)
    best_candidate = text
    best_score = _score_text_quality(text)

    for encoding in ("latin1", "cp1252"):
        repair_source = _drop_unencodable_characters(text, encoding)
        if not repair_source:
            continue

        try:
            repaired = repair_source.encode(encoding).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue

        repaired_suspicious_count = sum(
            repaired.count(marker) for marker in _SUSPICIOUS_MOJIBAKE_MARKERS
        )
        repaired_cjk_count = sum(1 for char in repaired if "\u4e00" <= char <= "\u9fff")

        if repaired_cjk_count > 0 and repaired_suspicious_count < original_suspicious_count:
            return repaired

        repaired_score = _score_text_quality(repaired)
        if repaired_score > best_score:
            best_candidate = repaired
            best_score = repaired_score

    return best_candidate


def clean_text(text: str | None) -> str:
    """按固定顺序执行反转义、乱码修复、字符过滤和空白标准化。"""
    if text is None:
        return ""

    normalized = unescape(str(text))
    normalized = repair_mojibake(normalized)
    normalized = strip_invalid_characters(normalized)
    normalized = normalize_whitespace(normalized)
    return normalized.strip()
