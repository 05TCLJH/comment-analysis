"""Hacker News 采集器模块：通过公开接口抓取评论原始数据。"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from comment_analysis.crawlers.base import BaseCrawler
from comment_analysis.models import CommentRecord
from comment_analysis.parsers import HackerNewsCommentParser


class HackerNewsCommentCrawler(BaseCrawler):
    """使用公开搜索接口抓取 Hacker News 评论。"""

    platform_name = "hackernews"
    api_url = "https://hn.algolia.com/api/v1/search_by_date"

    def __init__(
        self,
        keyword: str,
        search_query: str | None = None,
        max_records: int = 20,
        timeout: float = 10.0,
        user_agent: str = "comment-analysis/0.1",
    ) -> None:
        self.keyword = keyword.strip() or "美以伊战争"
        self.search_query = (search_query or self.keyword).strip() or self.keyword
        self.max_records = max(1, min(max_records, 100))
        self.timeout = timeout
        self.user_agent = user_agent
        self.parser = HackerNewsCommentParser(
            keyword=self.keyword,
            search_query=self.search_query,
        )

    def _build_request_url(self) -> str:
        """生成公开搜索接口的请求地址。"""
        query = urlencode(
            {
                "tags": "comment",
                "query": self.search_query,
                "hitsPerPage": self.max_records,
            }
        )
        return f"{self.api_url}?{query}"

    def _fetch_payload(self) -> dict[str, Any]:
        """请求远端接口并返回解析后的字典结果。"""
        request = Request(
            self._build_request_url(),
            headers={"User-Agent": self.user_agent},
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"抓取 Hacker News 评论失败：{exc}") from exc

        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Hacker News 返回的数据不是合法 JSON") from exc

        if not isinstance(data, dict):
            raise RuntimeError("Hacker News 返回的数据结构不符合预期")
        return data

    def _build_parse_items(
        self,
        hits: list[dict[str, Any]],
        crawl_time: datetime,
    ) -> list[dict[str, Any]]:
        """把原始命中项包装成解析器需要的输入结构。"""
        return [
            {
                "hit": hit,
                "crawl_time": crawl_time,
            }
            for hit in hits
        ]

    def crawl(self) -> list[CommentRecord]:
        """执行抓取流程并返回评论对象列表。"""
        payload = self._fetch_payload()
        hits = payload.get("hits", [])
        if not isinstance(hits, list):
            raise RuntimeError("Hacker News 返回的评论列表格式不正确")

        valid_hits = [hit for hit in hits if isinstance(hit, dict)]
        crawl_time = datetime.now()
        return self.parser.parse_many(self._build_parse_items(valid_hits, crawl_time))
