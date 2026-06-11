"""Stack Exchange 采集器：抓取政治站点上的问答评论。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from comment_analysis.crawlers.base import BaseCrawler
from comment_analysis.models import CommentRecord
from comment_analysis.parsers import StackExchangeCommentParser


class StackExchangeCommentCrawler(BaseCrawler):
    """使用公开 API 抓取 Stack Exchange 评论。"""

    platform_name = "stackexchange"
    api_base_url = "https://api.stackexchange.com/2.3"
    default_site = "politics"

    def __init__(
        self,
        keyword: str,
        search_query: str | None = None,
        site: str = default_site,
        max_records: int = 20,
        timeout: float = 10.0,
        user_agent: str = "comment-analysis/0.1",
    ) -> None:
        self.keyword = keyword.strip() or "美以伊战争"
        self.search_query = (search_query or self.keyword).strip() or self.keyword
        self.site = site.strip() or self.default_site
        self.max_records = max(1, min(max_records, 100))
        self.timeout = timeout
        self.user_agent = user_agent
        self.parser = StackExchangeCommentParser(
            keyword=self.keyword,
            search_query=self.search_query,
            site=self.site,
        )

    def _build_search_url(self) -> str:
        """生成问题搜索接口地址。"""
        query = urlencode(
            {
                "site": self.site,
                "q": self.search_query,
                "pagesize": self.max_records,
                "order": "desc",
                "sort": "activity",
                "filter": "default",
            }
        )
        return f"{self.api_base_url}/search/advanced?{query}"

    def _build_comments_url(self, question_ids: list[str]) -> str:
        """生成批量评论接口地址。"""
        joined_ids = ";".join(question_ids)
        query = urlencode(
            {
                "site": self.site,
                "pagesize": self.max_records,
                "order": "desc",
                "sort": "creation",
                "filter": "withbody",
            }
        )
        return f"{self.api_base_url}/questions/{joined_ids}/comments?{query}"

    def _fetch_payload(self, url: str) -> dict[str, Any]:
        """请求远端接口并返回解析后的 JSON 数据。"""
        request = Request(url, headers={"User-Agent": self.user_agent})

        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"抓取 Stack Exchange 数据失败：{exc}") from exc

        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Stack Exchange 返回的数据不是合法 JSON") from exc

        if not isinstance(data, dict):
            raise RuntimeError("Stack Exchange 返回的数据结构不符合预期")
        return data

    def _extract_question_map(self, payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """把问题列表整理成方便查找的映射。"""
        question_map: dict[str, dict[str, Any]] = {}
        items = payload.get("items", [])
        if not isinstance(items, list):
            return question_map

        for item in items:
            if not isinstance(item, dict):
                continue
            question_id = item.get("question_id")
            if question_id is None:
                continue
            question_map[str(question_id)] = item
        return question_map

    def _build_parse_items(
        self,
        question_map: dict[str, dict[str, Any]],
        comments: list[dict[str, Any]],
        crawl_time: datetime,
    ) -> list[dict[str, Any]]:
        """把问题和评论组装成解析器需要的结构。"""
        parse_items: list[dict[str, Any]] = []
        for comment in comments:
            post_id = str(comment.get("post_id") or "").strip()
            question = question_map.get(post_id)
            if not question:
                continue
            parse_items.append(
                {
                    "question": question,
                    "comment": comment,
                    "crawl_time": crawl_time,
                }
            )
        return parse_items

    def crawl_with_raw(self) -> tuple[dict[str, Any], list[CommentRecord]]:
        """执行抓取流程并返回原始响应与评论列表。"""
        search_payload = self._fetch_payload(self._build_search_url())
        question_map = self._extract_question_map(search_payload)
        if not question_map:
            return {"search": search_payload, "comments": {"items": []}}, []

        comment_payload = self._fetch_payload(self._build_comments_url(list(question_map.keys())))
        comments = comment_payload.get("items", [])
        if not isinstance(comments, list):
            raise RuntimeError("Stack Exchange 返回的评论列表格式不正确")

        valid_comments = [comment for comment in comments if isinstance(comment, dict)]
        crawl_time = datetime.now(timezone.utc)
        records = self.parser.parse_many(
            self._build_parse_items(question_map, valid_comments, crawl_time)
        )
        return {"search": search_payload, "comments": comment_payload}, records

    def crawl(self) -> list[CommentRecord]:
        """执行抓取流程并返回评论列表。"""
        _, records = self.crawl_with_raw()
        return records
