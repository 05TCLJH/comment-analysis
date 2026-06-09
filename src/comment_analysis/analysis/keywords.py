"""关键词分析模块：提供关键词提取和高频词统计能力。"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
import re

from comment_analysis.models import CommentRecord


_ENGLISH_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9'-]{1,}")
_CHINESE_TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]{2,}")

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "were",
    "will",
    "with",
    "一个",
    "一种",
    "一些",
    "不是",
    "为了",
    "以及",
    "但是",
    "你们",
    "我们",
    "他们",
    "自己",
    "这个",
    "这个问题",
    "这些",
    "那个",
    "那些",
    "还是",
    "因为",
    "所以",
    "如果",
    "已经",
    "没有",
    "需要",
    "觉得",
    "很多",
    "就是",
    "一下",
}


def _extract_text_parts(record: CommentRecord) -> list[str]:
    """从评论对象中收集适合做关键词统计的文本。"""
    parts = [record.content]
    if record.title:
        parts.append(record.title)
    return parts


def tokenize_text(text: str) -> list[str]:
    """把中英文文本切分成适合统计的词项。"""
    tokens: list[str] = []

    for token in _ENGLISH_TOKEN_PATTERN.findall(text.lower()):
        normalized_token = token.strip("-'")
        if len(normalized_token) < 2:
            continue
        if normalized_token in _STOP_WORDS:
            continue
        tokens.append(normalized_token)

    for token in _CHINESE_TOKEN_PATTERN.findall(text):
        if token in _STOP_WORDS:
            continue
        tokens.append(token)

    return tokens


def extract_keywords_from_record(record: CommentRecord, top_n: int = 5) -> list[str]:
    """从单条评论中提取关键词。"""
    token_counter: Counter[str] = Counter()
    for text in _extract_text_parts(record):
        token_counter.update(tokenize_text(text))

    return [keyword for keyword, _ in token_counter.most_common(top_n)]


def assign_keywords(records: Iterable[CommentRecord], top_n: int = 5) -> list[CommentRecord]:
    """为每条评论回填关键词字段。"""
    updated_records: list[CommentRecord] = []
    for record in records:
        keywords = extract_keywords_from_record(record, top_n=top_n)
        updated_record = CommentRecord(
            platform=record.platform,
            content=record.content,
            source_url=record.source_url,
            crawl_time=record.crawl_time,
            title=record.title,
            author=record.author,
            author_id=record.author_id,
            comment_id=record.comment_id,
            publish_time=record.publish_time,
            like_count=record.like_count,
            reply_count=record.reply_count,
            sentiment_label=record.sentiment_label,
            keywords=keywords,
            raw_data=record.raw_data,
        )
        updated_records.append(updated_record)
    return updated_records


def build_keyword_report(records: Iterable[CommentRecord], top_n: int = 20) -> dict[str, object]:
    """统计评论中的高频关键词并返回分析结果。"""
    records_list = list(records)
    token_counter: Counter[str] = Counter()

    for record in records_list:
        for text in _extract_text_parts(record):
            token_counter.update(tokenize_text(text))

    top_keywords = [
        {
            "keyword": keyword,
            "count": count,
        }
        for keyword, count in token_counter.most_common(top_n)
    ]

    return {
        "total_records": len(records_list),
        "unique_keywords": len(token_counter),
        "top_keywords": top_keywords,
    }
