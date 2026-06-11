"""采集入口：运行单一或多源评论抓取流程。"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from comment_analysis.config.settings import settings
from comment_analysis.crawlers.bridge import CN_PLATFORMS, MediaCrawlerError, resolve_platforms
from comment_analysis.crawlers.sources import (
    HackerNewsCommentCrawler,
    MediaCrawlerTiebaCrawler,
    MediaCrawlerWeiboCrawler,
    MediaCrawlerZhihuCrawler,
    StackExchangeCommentCrawler,
)
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


def _default_job_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]


def _build_english_crawler(
    platform: str,
    *,
    keyword: str,
    search_query: str,
    max_records: int,
) -> object:
    user_agent = settings.user_agent or "comment-analysis/0.1"
    if platform == "hackernews":
        return HackerNewsCommentCrawler(
            keyword=keyword,
            search_query=search_query,
            max_records=max_records,
            user_agent=user_agent,
        )
    if platform == "stackexchange":
        return StackExchangeCommentCrawler(
            keyword=keyword,
            search_query=search_query,
            max_records=max_records,
            user_agent=user_agent,
        )
    raise ValueError(f"不支持的英文数据源：{platform}")


def _build_cn_crawler(
    platform: str,
    *,
    keyword: str,
    max_records: int,
    job_id: str,
) -> object:
    common_kwargs = {
        "keyword": keyword,
        "max_records": max_records,
        "job_id": job_id,
        "raw_dir": settings.raw_dir,
    }
    if platform == "tieba":
        return MediaCrawlerTiebaCrawler(**common_kwargs)
    if platform == "zhihu":
        return MediaCrawlerZhihuCrawler(**common_kwargs)
    if platform == "weibo":
        return MediaCrawlerWeiboCrawler(**common_kwargs)
    raise ValueError(f"不支持的中文数据源：{platform}")


def _build_crawlers(
    keyword: str,
    max_records: int,
    source: str,
    job_id: str,
) -> list[object]:
    """根据来源名称构建对应的采集器列表。"""
    normalized_keyword = keyword.strip() or "美以伊战争"
    search_query = _resolve_search_query(normalized_keyword)
    platforms = resolve_platforms(source)

    crawlers: list[object] = []
    for platform in platforms:
        if platform in CN_PLATFORMS:
            crawlers.append(
                _build_cn_crawler(
                    platform,
                    keyword=normalized_keyword,
                    max_records=max_records,
                    job_id=job_id,
                )
            )
        else:
            crawlers.append(
                _build_english_crawler(
                    platform,
                    keyword=normalized_keyword,
                    search_query=search_query,
                    max_records=max_records,
                )
            )
    return crawlers


def collect_with_raw(
    keyword: str = "美以伊战争",
    max_records: int = 20,
    source: str = "hackernews",
    job_id: str | None = None,
) -> list[dict[str, object]]:
    """采集并返回各平台的 raw payload 与 CommentRecord 列表。"""
    effective_job_id = job_id or _default_job_id()
    bundles: list[dict[str, object]] = []
    for crawler in _build_crawlers(
        keyword=keyword,
        max_records=max_records,
        source=source,
        job_id=effective_job_id,
    ):
        try:
            raw_payload, records = crawler.crawl_with_raw()
            bundles.append(
                {
                    "platform": crawler.platform_name,
                    "raw_payload": raw_payload,
                    "records": records,
                }
            )
        except MediaCrawlerError as exc:
            if crawler.platform_name not in CN_PLATFORMS:
                raise
            bundles.append(
                {
                    "platform": crawler.platform_name,
                    "raw_payload": {"error": str(exc)},
                    "records": [],
                }
            )
        finally:
            crawler.close()
    return bundles


def collect_records(
    keyword: str = "美以伊战争",
    max_records: int = 20,
    source: str = "hackernews",
    job_id: str | None = None,
) -> list[CommentRecord]:
    """运行真实数据源采集流程并返回标准评论列表。"""
    records: list[CommentRecord] = []
    for bundle in collect_with_raw(
        keyword=keyword,
        max_records=max_records,
        source=source,
        job_id=job_id,
    ):
        records.extend(bundle["records"])
    return records
