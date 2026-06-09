"""Hacker News 解析器模块：把接口返回结果转换为标准评论对象。"""

from __future__ import annotations

import re
from datetime import datetime
from html import unescape
from typing import Any

from comment_analysis.models import CommentRecord
from comment_analysis.parsers.base import BaseParser


class HackerNewsCommentParser(BaseParser):
    """负责解析 Hacker News 评论接口中的单条命中项。"""

    def __init__(self, keyword: str, search_query: str) -> None:
        self.keyword = keyword.strip() or "美以伊战争"
        self.search_query = search_query.strip() or self.keyword

    def _clean_text(self, content: str | None) -> str:
        """清理评论内容中的标签、实体和多余空白。"""
        if not content:
            return ""
        text = re.sub(r"<[^>]+>", " ", content)
        text = unescape(text)
        return " ".join(text.split())

    def _build_source_url(self, hit: dict[str, Any]) -> str:
        """优先返回原文地址，缺失时回退到评论详情页。"""
        story_url = str(hit.get("story_url") or "").strip()
        if story_url:
            return story_url

        story_id = str(hit.get("story_id") or "").strip()
        if story_id:
            return f"https://news.ycombinator.com/item?id={story_id}"

        comment_id = str(hit.get("objectID") or "").strip()
        if comment_id:
            return f"https://news.ycombinator.com/item?id={comment_id}"

        return "https://news.ycombinator.com/"

    def parse(self, raw_item: Any) -> CommentRecord | None:
        """把单条命中项解析成标准评论对象。"""
        if not isinstance(raw_item, dict):
            return None

        hit = raw_item.get("hit")
        crawl_time = raw_item.get("crawl_time")
        if not isinstance(hit, dict):
            return None
        if not isinstance(crawl_time, datetime):
            crawl_time = datetime.now()

        content = self._clean_text(hit.get("comment_text"))
        if not content:
            return None

        author = str(hit.get("author") or "").strip() or None
        comment_id = str(hit.get("objectID") or "").strip() or None
        title = self._clean_text(str(hit.get("story_title") or "").strip()) or None

        return CommentRecord(
            platform="hackernews",
            content=content,
            source_url=self._build_source_url(hit),
            crawl_time=crawl_time,
            title=title,
            author=author,
            comment_id=comment_id,
            publish_time=hit.get("created_at"),
            raw_data={
                "keyword": self.keyword,
                "search_query": self.search_query,
                "source_item": hit,
            },
        )
