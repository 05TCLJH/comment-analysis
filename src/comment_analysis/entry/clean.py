"""清洗入口：提供评论去重、去空值、时间统一和字符清洗流程。"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from comment_analysis.models import CommentRecord
from comment_analysis.utils.text import clean_text


def _parse_datetime_value(value: Any) -> datetime | None:
    """把原始时间值尽量解析为日期时间对象。"""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value

    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _normalize_datetime_value(value: datetime | None) -> datetime | None:
    """统一时间精度，并把带时区的时间转换到 UTC。"""
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc)
    return value.replace(microsecond=0)


def _resolve_publish_time(record: CommentRecord) -> datetime | None:
    """优先使用模型中的发布时间，缺失时尝试从原始数据回填。"""
    publish_time = _normalize_datetime_value(record.publish_time)
    if publish_time is not None:
        return publish_time

    raw_data = record.raw_data if isinstance(record.raw_data, Mapping) else {}
    source_item = raw_data.get("source_item")
    if isinstance(source_item, Mapping):
        for field_name in ("created_at", "publish_time", "time"):
            parsed = _parse_datetime_value(source_item.get(field_name))
            normalized = _normalize_datetime_value(parsed)
            if normalized is not None:
                return normalized

    return None


def _build_content_key(record: CommentRecord) -> tuple[str, str, str]:
    """按平台、链接和内容构造去重键。"""
    return (
        record.platform,
        record.source_url,
        record.content,
    )


def _build_comment_key(record: CommentRecord) -> tuple[str, str] | None:
    """按平台和评论编号构造去重键。"""
    if not record.comment_id:
        return None
    return (record.platform, record.comment_id)


def _clean_single_record(record: CommentRecord) -> CommentRecord | None:
    """对单条评论执行基础清洗。"""
    content = clean_text(record.content)
    source_url = clean_text(record.source_url)

    if not content or not source_url:
        return None

    title = clean_text(record.title) or None
    author = clean_text(record.author) or None
    author_id = clean_text(record.author_id) or None
    comment_id = clean_text(record.comment_id) or None
    sentiment_label = clean_text(record.sentiment_label) or None

    keywords = [keyword for keyword in (clean_text(keyword) for keyword in record.keywords) if keyword]
    raw_data = dict(record.raw_data) if isinstance(record.raw_data, Mapping) else {}

    return CommentRecord(
        platform=record.platform,
        content=content,
        source_url=source_url,
        crawl_time=_normalize_datetime_value(record.crawl_time) or record.crawl_time,
        title=title,
        author=author,
        author_id=author_id,
        comment_id=comment_id,
        publish_time=_resolve_publish_time(record),
        like_count=record.like_count,
        reply_count=record.reply_count,
        sentiment_label=sentiment_label,
        keywords=keywords,
        raw_data=raw_data,
    )


def clean_records(records: Iterable[CommentRecord]) -> list[CommentRecord]:
    """执行去空值、时间统一、乱码修复、字符过滤和去重逻辑。"""
    cleaned_records: list[CommentRecord] = []
    seen_content_keys: set[tuple[str, str, str]] = set()
    seen_comment_keys: set[tuple[str, str]] = set()

    for record in records:
        normalized_record = _clean_single_record(record)
        if normalized_record is None:
            continue

        comment_key = _build_comment_key(normalized_record)
        content_key = _build_content_key(normalized_record)

        if comment_key is not None and comment_key in seen_comment_keys:
            continue
        if content_key in seen_content_keys:
            continue

        if comment_key is not None:
            seen_comment_keys.add(comment_key)
        seen_content_keys.add(content_key)
        cleaned_records.append(normalized_record)

    return cleaned_records
