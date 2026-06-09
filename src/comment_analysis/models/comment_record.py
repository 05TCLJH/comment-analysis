"""评论数据模型：定义项目内统一使用的评论结构。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


def _normalize_required_text(value: Any, field_name: str) -> str:
    """把必填文本转成去除首尾空白后的字符串。"""
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError(f"{field_name} 不能为空")
    return text


def _normalize_optional_text(value: Any) -> str | None:
    """把可选文本转成去除首尾空白后的字符串。"""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_int(value: Any) -> int | None:
    """把点赞数、回复数等字段统一转换为整数。"""
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
    except ValueError as exc:
        raise ValueError(f"无法把 {value!r} 转换为整数") from exc


def _parse_datetime(value: Any, field_name: str) -> datetime | None:
    """把常见时间输入统一解析为 `datetime` 对象。"""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())

    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"无法从 {value!r} 解析字段 {field_name}") from exc


def _normalize_keywords(value: Any) -> list[str]:
    """把关键词统一整理成去重后的字符串列表。"""
    if value is None or value == "":
        return []
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, Sequence):
        items = list(value)
    else:
        items = [value]

    result: list[str] = []
    for item in items:
        text = str(item).strip()
        if text and text not in result:
            result.append(text)
    return result


def _serialize_value(value: Any) -> Any:
    """把时间和嵌套结构转换为适合存储的普通数据。"""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _serialize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize_value(item) for item in value]
    return value


@dataclass(slots=True)
class CommentRecord:
    """爬虫、解析、清洗和分析阶段共用的标准评论对象。"""

    platform: str
    content: str
    source_url: str
    crawl_time: datetime

    title: str | None = None
    author: str | None = None
    author_id: str | None = None
    comment_id: str | None = None
    publish_time: datetime | None = None
    like_count: int | None = None
    reply_count: int | None = None
    sentiment_label: str | None = None
    keywords: list[str] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """在对象创建后统一清洗和校验字段。"""
        self.platform = _normalize_required_text(self.platform, "platform")
        self.content = _normalize_required_text(self.content, "content")
        self.source_url = _normalize_required_text(self.source_url, "source_url")

        parsed_crawl_time = _parse_datetime(self.crawl_time, "crawl_time")
        if parsed_crawl_time is None:
            raise ValueError("crawl_time 不能为空")
        self.crawl_time = parsed_crawl_time

        self.title = _normalize_optional_text(self.title)
        self.author = _normalize_optional_text(self.author)
        self.author_id = _normalize_optional_text(self.author_id)
        self.comment_id = _normalize_optional_text(self.comment_id)
        self.publish_time = _parse_datetime(self.publish_time, "publish_time")
        self.like_count = _coerce_int(self.like_count)
        self.reply_count = _coerce_int(self.reply_count)
        self.sentiment_label = _normalize_optional_text(self.sentiment_label)
        self.keywords = _normalize_keywords(self.keywords)
        self.raw_data = dict(self.raw_data) if isinstance(self.raw_data, Mapping) else {}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CommentRecord":
        """从字典构建标准评论对象。"""
        payload = dict(data)
        raw_data = payload.get("raw_data")
        if not isinstance(raw_data, Mapping):
            raw_data = payload

        crawl_time = _parse_datetime(payload.get("crawl_time"), "crawl_time")
        if crawl_time is None:
            raise ValueError("crawl_time 不能为空")

        return cls(
            platform=_normalize_required_text(payload.get("platform"), "platform"),
            content=_normalize_required_text(payload.get("content"), "content"),
            source_url=_normalize_required_text(payload.get("source_url"), "source_url"),
            crawl_time=crawl_time,
            title=_normalize_optional_text(payload.get("title")),
            author=_normalize_optional_text(payload.get("author")),
            author_id=_normalize_optional_text(payload.get("author_id")),
            comment_id=_normalize_optional_text(payload.get("comment_id")),
            publish_time=_parse_datetime(payload.get("publish_time"), "publish_time"),
            like_count=_coerce_int(payload.get("like_count")),
            reply_count=_coerce_int(payload.get("reply_count")),
            sentiment_label=_normalize_optional_text(payload.get("sentiment_label")),
            keywords=_normalize_keywords(payload.get("keywords")),
            raw_data=dict(raw_data),
        )

    def to_dict(self) -> dict[str, Any]:
        """把评论对象转换为适合持久化的普通字典。"""
        return {
            "platform": self.platform,
            "content": self.content,
            "source_url": self.source_url,
            "crawl_time": _serialize_value(self.crawl_time),
            "title": self.title,
            "author": self.author,
            "author_id": self.author_id,
            "comment_id": self.comment_id,
            "publish_time": _serialize_value(self.publish_time),
            "like_count": self.like_count,
            "reply_count": self.reply_count,
            "sentiment_label": self.sentiment_label,
            "keywords": _serialize_value(self.keywords),
            "raw_data": _serialize_value(self.raw_data),
        }
