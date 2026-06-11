"""情感分析模块：提供轻量级情感分类能力。"""

from __future__ import annotations

from collections.abc import Iterable

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from comment_analysis.analysis.language import LanguageLabel, detect_language
from comment_analysis.analysis.nltk_data import ensure_nltk_data
from comment_analysis.analysis.tokenize_cn import tokenize_chinese
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

_analyzer: SentimentIntensityAnalyzer | None = None


def _collect_text(record: CommentRecord) -> str:
    """把用于情感分析的文本字段拼接起来。"""
    parts = [record.content]
    if record.title:
        parts.append(record.title)
    return " ".join(part for part in parts if part)


def _get_vader() -> SentimentIntensityAnalyzer:
    global _analyzer
    if _analyzer is None:
        ensure_nltk_data()
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer


def _classify_chinese(text: str) -> tuple[str, int]:
    """沿用词典 + 否定词规则（使用 jieba 分词提升命中率）。"""
    tokens = tokenize_chinese(text)
    score = 0
    for index, token in enumerate(tokens):
        previous = tokens[index - 1] if index > 0 else ""
        reverse = previous in _NEGATION_WORDS or any(
            token.startswith(neg) for neg in _NEGATION_WORDS if len(neg) == 1
        )
        if token in _POSITIVE_WORDS:
            score += -1 if reverse else 1
        elif token in _NEGATIVE_WORDS:
            score += 1 if reverse else -1
    if score >= 2:
        return "积极", score
    if score <= -2:
        return "消极", score
    return "中性", score


def _classify_english(text: str) -> tuple[str, int]:
    """VADER compound 分数映射为三分类。"""
    compound = _get_vader().polarity_scores(text)["compound"]
    scaled = int(round(compound * 10))
    if compound >= 0.05:
        return "积极", scaled
    if compound <= -0.05:
        return "消极", scaled
    return "中性", scaled


def classify_sentiment(text: str) -> tuple[str, int]:
    """按主语言选择情感管线；混合文本优先中文词典（含英文负面词）。"""
    label = detect_language(text)
    if label == LanguageLabel.ZH:
        return _classify_chinese(text)
    if label == LanguageLabel.EN:
        return _classify_english(text)
    if label == LanguageLabel.MIXED:
        zh_label, zh_score = _classify_chinese(text)
        en_label, en_score = _classify_english(text)
        if abs(en_score) > abs(zh_score):
            return en_label, en_score
        return zh_label, zh_score
    return _classify_english(text)


def assign_sentiment(records: Iterable[CommentRecord]) -> list[CommentRecord]:
    """为每条评论补充情感标签。"""
    updated_records: list[CommentRecord] = []
    for record in records:
        text = _collect_text(record)
        sentiment_label, score = classify_sentiment(text)
        raw_data = dict(record.raw_data)
        raw_data["sentiment_score"] = score
        raw_data["detected_language"] = detect_language(text).value

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
                sentiment_label=sentiment_label,
                keywords=record.keywords,
                raw_data=raw_data,
            )
        )
    return updated_records
