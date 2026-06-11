"""MediaCrawler JSONL 解析公共工具。"""

from __future__ import annotations

import re
from datetime import datetime
from html import unescape
from typing import Any


def clean_html_text(value: Any) -> str:
    """去除 HTML 标签并规范化空白。"""
    if value is None:
        return ""
    text = unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def parse_timestamp(value: Any) -> datetime | None:
    """解析 Unix 时间戳或 ISO 字符串。"""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value))
        except (OSError, OverflowError, ValueError):
            return None

    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        try:
            return datetime.fromtimestamp(int(text))
        except (OSError, OverflowError, ValueError):
            return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def coerce_int(value: Any) -> int | None:
    """把点赞数、回复数等字段转为整数。"""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None
