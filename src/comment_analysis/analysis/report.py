"""分析汇总模块：构建多维度统计结果。"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import datetime
from statistics import fmean
from typing import Any

from comment_analysis.analysis.keywords import build_keyword_report
from comment_analysis.models import CommentRecord


def _get_date_label(record: CommentRecord) -> str | None:
    """获取用于趋势统计的日期标签。"""
    value = record.publish_time or record.crawl_time
    if not isinstance(value, datetime):
        return None
    return value.date().isoformat()


def _normalize_record(record: CommentRecord) -> dict[str, Any]:
    """把记录整理成适合展示层使用的普通字典。"""
    date_label = _get_date_label(record)
    return {
        "platform": record.platform,
        "content": record.content,
        "source_url": record.source_url,
        "crawl_time": record.crawl_time.isoformat(),
        "title": record.title,
        "author": record.author,
        "author_id": record.author_id,
        "comment_id": record.comment_id,
        "publish_time": record.publish_time.isoformat() if record.publish_time else None,
        "date_label": date_label,
        "like_count": record.like_count,
        "reply_count": record.reply_count,
        "sentiment_label": record.sentiment_label or "中性",
        "keywords": list(record.keywords),
    }


def _to_series(counter: Counter[str], *, sort_by_count: bool = True) -> list[dict[str, Any]]:
    """把计数器转换成列表结构。"""
    items = counter.items()
    if sort_by_count:
        ordered = sorted(items, key=lambda item: (-item[1], item[0]))
    else:
        ordered = sorted(items, key=lambda item: item[0])
    return [{"label": label, "count": count} for label, count in ordered]


def build_analysis_report(records: Iterable[CommentRecord], top_n: int = 20) -> dict[str, Any]:
    """基于评论列表构建多维度分析报告。"""
    records_list = list(records)
    keyword_report = build_keyword_report(records_list, top_n=top_n)

    platform_counter: Counter[str] = Counter()
    sentiment_counter: Counter[str] = Counter()
    daily_counter: Counter[str] = Counter()
    platform_sentiment_counter: dict[str, Counter[str]] = defaultdict(Counter)
    daily_sentiment_counter: dict[str, Counter[str]] = defaultdict(Counter)
    keyword_sentiment_counter: dict[str, Counter[str]] = defaultdict(Counter)
    keyword_platform_counter: dict[str, Counter[str]] = defaultdict(Counter)

    like_values: list[int] = []
    reply_values: list[int] = []
    normalized_records: list[dict[str, Any]] = []
    date_labels: list[str] = []

    for record in records_list:
        sentiment_label = record.sentiment_label or "中性"
        date_label = _get_date_label(record)

        platform_counter.update([record.platform])
        sentiment_counter.update([sentiment_label])

        if date_label:
            daily_counter.update([date_label])
            daily_sentiment_counter[date_label].update([sentiment_label])
            date_labels.append(date_label)

        platform_sentiment_counter[record.platform].update([sentiment_label])

        for keyword in record.keywords:
            keyword_sentiment_counter[keyword].update([sentiment_label])
            keyword_platform_counter[keyword].update([record.platform])

        if record.like_count is not None:
            like_values.append(record.like_count)
        if record.reply_count is not None:
            reply_values.append(record.reply_count)

        normalized_records.append(_normalize_record(record))

    top_keyword_names = [item["keyword"] for item in keyword_report["top_keywords"]]

    platform_sentiment_breakdown = []
    for platform, counter in sorted(platform_sentiment_counter.items(), key=lambda item: item[0]):
        platform_sentiment_breakdown.append(
            {
                "platform": platform,
                "total": sum(counter.values()),
                "breakdown": _to_series(counter),
            }
        )

    daily_sentiment_breakdown = []
    for date_label, counter in sorted(daily_sentiment_counter.items(), key=lambda item: item[0]):
        daily_sentiment_breakdown.append(
            {
                "date": date_label,
                "total": sum(counter.values()),
                "breakdown": _to_series(counter),
            }
        )

    keyword_sentiment_breakdown = []
    for keyword in top_keyword_names:
        sentiment_breakdown = keyword_sentiment_counter.get(keyword, Counter())
        platform_breakdown = keyword_platform_counter.get(keyword, Counter())
        keyword_sentiment_breakdown.append(
            {
                "keyword": keyword,
                "total": sum(sentiment_breakdown.values()),
                "sentiments": _to_series(sentiment_breakdown),
                "platforms": _to_series(platform_breakdown),
            }
        )

    date_range = {
        "start": min(date_labels) if date_labels else None,
        "end": max(date_labels) if date_labels else None,
    }

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_records": len(records_list),
        "unique_keywords": keyword_report["unique_keywords"],
        "top_keywords": keyword_report["top_keywords"],
        "platform_distribution": _to_series(platform_counter),
        "sentiment_distribution": _to_series(sentiment_counter),
        "daily_trend": _to_series(daily_counter, sort_by_count=False),
        "platform_sentiment_breakdown": platform_sentiment_breakdown,
        "daily_sentiment_breakdown": daily_sentiment_breakdown,
        "keyword_sentiment_breakdown": keyword_sentiment_breakdown,
        "date_range": date_range,
        "records": normalized_records,
        "platform_count": len(platform_counter),
        "publish_time_count": sum(1 for record in records_list if record.publish_time is not None),
        "like_count_count": len(like_values),
        "reply_count_count": len(reply_values),
        "average_like_count": fmean(like_values) if like_values else None,
        "average_reply_count": fmean(reply_values) if reply_values else None,
        "filter_options": {
            "platforms": sorted(platform_counter.keys()),
            "sentiments": [item["label"] for item in _to_series(sentiment_counter)],
        },
    }
