"""规则化洞察生成：基于统计结果产出可读分析摘要（无 LLM）。"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable
from datetime import date, datetime, timedelta
from typing import Any

from comment_analysis.models import CommentRecord

_SENTIMENT_LABELS = ("积极", "中性", "消极")
_MIN_PLATFORM_COMMENTS = 5


def _dominant_sentiment(sentiments: list[dict[str, Any]]) -> str:
    """从情感分布列表中选出占比最高的标签。"""
    if not sentiments:
        return "中性"
    ordered = sorted(sentiments, key=lambda item: (-item["count"], item["label"]))
    return str(ordered[0]["label"])


def _percentile(values: list[int], percentile: float) -> int:
    """计算整数列表的百分位值（含端点插值）。"""
    if not values:
        raise ValueError("values 不能为空")
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile / 100
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return int(round(ordered[lower] * (1 - weight) + ordered[upper] * weight))


def _get_date_label(record: CommentRecord) -> str | None:
    """获取用于趋势统计的日期标签。"""
    value = record.publish_time or record.crawl_time
    if not isinstance(value, datetime):
        return None
    return value.date().isoformat()


def _insight(
    *,
    insight_id: str,
    title: str,
    body: str,
    kind: str,
    priority: int,
) -> dict[str, Any]:
    """构造单条洞察字典。"""
    return {
        "id": insight_id,
        "title": title,
        "body": body,
        "kind": kind,
        "priority": priority,
    }


def _insight_platform_negative(
    platform_sentiment_breakdown: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """消极占比最高的平台（需该平台至少 5 条评论）。"""
    candidates: list[tuple[str, float, int, int]] = []
    for item in platform_sentiment_breakdown:
        total = int(item["total"])
        if total < _MIN_PLATFORM_COMMENTS:
            continue
        breakdown = {entry["label"]: entry["count"] for entry in item["breakdown"]}
        negative_count = breakdown.get("消极", 0)
        ratio = negative_count / total
        candidates.append((str(item["platform"]), ratio, negative_count, total))

    if not candidates:
        return None

    platform, ratio, negative_count, total = max(candidates, key=lambda row: (row[1], row[3]))
    pct = round(ratio * 100, 1)
    return _insight(
        insight_id="platform-most-negative",
        title=f"「{platform}」消极评论占比最高",
        body=(
            f"在 {total} 条评论中，{negative_count} 条为消极情感，"
            f"占比 {pct}%，高于其他样本量足够的平台。"
        ),
        kind="platform",
        priority=1,
    )


def _insight_top_keyword(
    top_keywords: list[dict[str, Any]],
    keyword_sentiment_breakdown: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """最高频关键词及其情感倾向。"""
    if not top_keywords:
        return None

    top_keyword = str(top_keywords[0]["keyword"])
    count = int(top_keywords[0]["count"])
    breakdown_map = {item["keyword"]: item for item in keyword_sentiment_breakdown}
    sentiment_info = breakdown_map.get(top_keyword, {})
    dominant = _dominant_sentiment(sentiment_info.get("sentiments", []))
    return _insight(
        insight_id="keyword-top-frequency",
        title=f"最高频词「{top_keyword}」",
        body=f"关键词「{top_keyword}」出现 {count} 次，关联评论以{dominant}情感为主。",
        kind="keyword",
        priority=2,
    )


def _insight_volume_trend(records: Iterable[CommentRecord]) -> dict[str, Any] | None:
    """近 7 日 vs 之前评论量变化。"""
    date_counter: Counter[str] = Counter()
    for record in records:
        label = _get_date_label(record)
        if label:
            date_counter.update([label])

    if len(date_counter) < 2:
        return None

    latest = max(date.fromisoformat(label) for label in date_counter)
    cutoff = latest - timedelta(days=6)
    recent_count = 0
    previous_count = 0
    for label, count in date_counter.items():
        day = date.fromisoformat(label)
        if day >= cutoff:
            recent_count += count
        else:
            previous_count += count

    if previous_count == 0:
        return None

    change_pct = round((recent_count - previous_count) / previous_count * 100, 1)
    direction = "上升" if change_pct > 0 else "下降" if change_pct < 0 else "持平"
    return _insight(
        insight_id="trend-volume-7d",
        title="近 7 日评论量变化",
        body=(
            f"最近 7 日共 {recent_count} 条评论，"
            f"较此前 {previous_count} 条{direction} {abs(change_pct)}%。"
        ),
        kind="trend",
        priority=3,
    )


def _insight_high_engagement_negative(records: Iterable[CommentRecord]) -> dict[str, Any] | None:
    """高互动评论（like_count >= P90）中消极占比。"""
    records_with_likes = [record for record in records if record.like_count is not None]
    if len(records_with_likes) < 5:
        return None

    like_values = [record.like_count for record in records_with_likes if record.like_count is not None]
    threshold = _percentile(like_values, 90)
    high_engagement = [record for record in records_with_likes if record.like_count >= threshold]
    if not high_engagement:
        return None

    negative_count = sum(
        1 for record in high_engagement if (record.sentiment_label or "中性") == "消极"
    )
    total = len(high_engagement)
    ratio = negative_count / total
    pct = round(ratio * 100, 1)
    return _insight(
        insight_id="engagement-high-like-negative",
        title="高互动评论情感分布",
        body=(
            f"点赞数 ≥ {threshold} 的高互动评论共 {total} 条，"
            f"其中 {negative_count} 条为消极（{pct}%）。"
        ),
        kind="engagement",
        priority=4,
    )


def generate_insights(
    records: Iterable[CommentRecord],
    *,
    top_keywords: list[dict[str, Any]],
    keyword_sentiment_breakdown: list[dict[str, Any]],
    platform_sentiment_breakdown: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """基于规则生成至少 3 条洞察（在数据允许时）。"""
    records_list = list(records)
    builders = [
        lambda: _insight_platform_negative(platform_sentiment_breakdown),
        lambda: _insight_top_keyword(top_keywords, keyword_sentiment_breakdown),
        lambda: _insight_volume_trend(records_list),
        lambda: _insight_high_engagement_negative(records_list),
    ]

    insights: list[dict[str, Any]] = []
    for builder in builders:
        insight = builder()
        if insight is not None:
            insights.append(insight)

    insights.sort(key=lambda item: item["priority"])
    return insights


def build_word_cloud(
    top_keywords: list[dict[str, Any]],
    keyword_sentiment_breakdown: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """从高频词与情感分布构建词云数据。"""
    breakdown_map = {item["keyword"]: item for item in keyword_sentiment_breakdown}
    word_cloud: list[dict[str, Any]] = []
    for item in top_keywords:
        keyword = str(item["keyword"])
        sentiment_info = breakdown_map.get(keyword, {})
        dominant = _dominant_sentiment(sentiment_info.get("sentiments", []))
        if dominant not in _SENTIMENT_LABELS:
            dominant = "中性"
        word_cloud.append(
            {
                "name": keyword,
                "value": int(item["count"]),
                "dominant_sentiment": dominant,
            }
        )
    return word_cloud


def build_sentiment_score_summary(records: Iterable[CommentRecord]) -> dict[str, Any]:
    """汇总 sentiment_score 的全局与分平台统计。"""
    from statistics import fmean

    scores: list[int] = []
    by_platform_scores: dict[str, list[int]] = {}

    for record in records:
        raw_score = record.raw_data.get("sentiment_score")
        if raw_score is None:
            continue
        score = int(raw_score)
        scores.append(score)
        by_platform_scores.setdefault(record.platform, []).append(score)

    if not scores:
        return {
            "min": None,
            "max": None,
            "avg": None,
            "histogram": [],
            "by_platform": [],
        }

    histogram: list[dict[str, int]] = []
    for bin_start in range(-10, 10, 2):
        bin_end = bin_start + 2
        if bin_end == 10:
            count = sum(1 for score in scores if bin_start <= score <= bin_end)
        else:
            count = sum(1 for score in scores if bin_start <= score < bin_end)
        histogram.append({"bin_start": bin_start, "bin_end": bin_end, "count": count})

    by_platform = [
        {
            "platform": platform,
            "avg": round(fmean(platform_scores), 2),
            "count": len(platform_scores),
        }
        for platform, platform_scores in sorted(by_platform_scores.items())
    ]

    return {
        "min": min(scores),
        "max": max(scores),
        "avg": round(fmean(scores), 2),
        "histogram": histogram,
        "by_platform": by_platform,
    }
