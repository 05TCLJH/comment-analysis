"""情感分析模块：提供轻量级情感分类能力。"""

from __future__ import annotations

from collections.abc import Iterable
import re

from comment_analysis.models import CommentRecord


_POSITIVE_WORDS = {
    "agree",
    "better",
    "calm",
    "clear",
    "good",
    "improve",
    "improved",
    "peace",
    "peaceful",
    "reasonable",
    "safe",
    "stable",
    "support",
    "supported",
    "trust",
    "win",
    "hope",
    "positive",
    "benefit",
    "合作",
    "稳定",
    "支持",
    "和平",
    "安全",
    "改善",
    "理性",
    "希望",
    "积极",
}

_NEGATIVE_WORDS = {
    "attack",
    "awful",
    "bad",
    "bomb",
    "chaos",
    "conflict",
    "critic",
    "criticism",
    "crisis",
    "danger",
    "death",
    "destabilised",
    "harm",
    "hate",
    "hostile",
    "kill",
    "risk",
    "spying",
    "threat",
    "unstable",
    "war",
    "wrong",
    "消极",
    "危险",
    "攻击",
    "战争",
    "混乱",
    "威胁",
    "伤害",
    "批评",
    "不安",
    "死亡",
}

_NEGATION_WORDS = {
    "not",
    "never",
    "no",
    "without",
    "hardly",
    "isn't",
    "don't",
    "can't",
    "不会",
    "不",
    "没",
    "没有",
}

_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9'-]{1,}|[\u4e00-\u9fff]{1,}")


def _collect_text(record: CommentRecord) -> str:
    """把用于情感分析的文本字段拼接起来。"""
    parts = [record.content]
    if record.title:
        parts.append(record.title)
    return " ".join(part for part in parts if part)


def _tokenize(text: str) -> list[str]:
    """将文本拆成中英文词项。"""
    return [token.strip().lower() for token in _TOKEN_PATTERN.findall(text) if token.strip()]


def classify_sentiment(text: str) -> tuple[str, int]:
    """对文本做简单词典情感分类，返回标签和分数。"""
    tokens = _tokenize(text)
    score = 0

    for index, token in enumerate(tokens):
        previous_token = tokens[index - 1] if index > 0 else ""
        reverse = previous_token in _NEGATION_WORDS

        if token in _POSITIVE_WORDS:
            score += -1 if reverse else 1
        elif token in _NEGATIVE_WORDS:
            score += 1 if reverse else -1

    if score >= 2:
        return "积极", score
    if score <= -2:
        return "消极", score
    return "中性", score


def assign_sentiment(records: Iterable[CommentRecord]) -> list[CommentRecord]:
    """为每条评论补充情感标签。"""
    updated_records: list[CommentRecord] = []
    for record in records:
        label, score = classify_sentiment(_collect_text(record))
        raw_data = dict(record.raw_data)
        raw_data["sentiment_score"] = score

        updated_records.append(
            CommentRecord(
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
                sentiment_label=label,
                keywords=record.keywords,
                raw_data=raw_data,
            )
        )
    return updated_records
