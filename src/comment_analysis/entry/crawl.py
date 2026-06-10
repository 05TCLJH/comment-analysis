"""采集入口：运行单一或多源评论抓取流程。"""

from __future__ import annotations

from comment_analysis.config.settings import settings
from comment_analysis.crawlers.sources import HackerNewsCommentCrawler, StackExchangeCommentCrawler
from comment_analysis.models import CommentRecord


def _contains_chinese(text: str) -> bool:
    """判断关键词中是否包含中文字符。"""
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _resolve_search_query(keyword: str) -> str:
    """把当前项目关键词映射为更适合英文数据源检索的查询词。"""
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


def _build_crawlers(keyword: str, max_records: int, source: str) -> list[object]:
    """根据来源名称构建对应的采集器列表。"""
    normalized_keyword = keyword.strip() or "美以伊战争"
    search_query = _resolve_search_query(normalized_keyword)
    normalized_source = source.strip().lower()

    if normalized_source == "hackernews":
        return [
            HackerNewsCommentCrawler(
                keyword=normalized_keyword,
                search_query=search_query,
                max_records=max_records,
                user_agent=settings.user_agent or "comment-analysis/0.1",
            )
        ]

    if normalized_source == "stackexchange":
        return [
            StackExchangeCommentCrawler(
                keyword=normalized_keyword,
                search_query=search_query,
                max_records=max_records,
                user_agent=settings.user_agent or "comment-analysis/0.1",
            )
        ]

    if normalized_source == "all":
        return [
            HackerNewsCommentCrawler(
                keyword=normalized_keyword,
                search_query=search_query,
                max_records=max_records,
                user_agent=settings.user_agent or "comment-analysis/0.1",
            ),
            StackExchangeCommentCrawler(
                keyword=normalized_keyword,
                search_query=search_query,
                max_records=max_records,
                user_agent=settings.user_agent or "comment-analysis/0.1",
            ),
        ]

    raise ValueError(f"不支持的数据源：{source}")


def collect_records(
    keyword: str = "美以伊战争",
    max_records: int = 20,
    source: str = "hackernews",
) -> list[CommentRecord]:
    """运行真实数据源采集流程并返回标准评论列表。"""
    records: list[CommentRecord] = []
    for crawler in _build_crawlers(keyword=keyword, max_records=max_records, source=source):
        try:
            records.extend(list(crawler.crawl()))
        finally:
            crawler.close()
    return records
