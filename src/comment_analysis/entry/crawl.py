"""采集入口：运行单一数据源的最小评论抓取流程。"""

from __future__ import annotations

from comment_analysis.config.settings import settings
from comment_analysis.crawlers.sources import HackerNewsCommentCrawler
from comment_analysis.models import CommentRecord


def _contains_chinese(text: str) -> bool:
    """判断关键词中是否包含中文字符。"""
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _resolve_search_query(keyword: str) -> str:
    """把当前项目关键词映射为更适合英文来源检索的查询词。"""
    normalized_keyword = keyword.strip() or "美以伊战争"
    query_mapping = {
        "美以伊战争": "Iran Israel war",
        "以伊战争": "Israel Iran conflict",
        "美伊战争": "US Iran conflict",
    }

    if normalized_keyword in query_mapping:
        return query_mapping[normalized_keyword]
    if _contains_chinese(normalized_keyword):
        return "Iran Israel war"
    return normalized_keyword


def collect_records(keyword: str = "美以伊战争", max_records: int = 20) -> list[CommentRecord]:
    """运行真实数据源采集流程并返回标准评论列表。"""
    normalized_keyword = keyword.strip() or "美以伊战争"
    crawler = HackerNewsCommentCrawler(
        keyword=normalized_keyword,
        search_query=_resolve_search_query(normalized_keyword),
        max_records=max_records,
        user_agent=settings.user_agent or "comment-analysis/0.1",
    )

    try:
        return list(crawler.crawl())
    finally:
        crawler.close()
