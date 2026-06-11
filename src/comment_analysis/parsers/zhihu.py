"""知乎 JSONL 解析器。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from comment_analysis.models import CommentRecord
from comment_analysis.parsers.base import BaseParser
from comment_analysis.parsers.mediacrawler_common import (
    clean_html_text,
    coerce_int,
    parse_timestamp,
)


class ZhihuCommentParser(BaseParser):
    """解析 MediaCrawler 知乎 comments JSONL。"""

    def __init__(self, keyword: str, content_index: dict[str, dict[str, Any]] | None = None) -> None:
        self.keyword = keyword.strip() or "美以伊战争"
        self.content_index = content_index or {}

    def _build_content_url(self, item: dict[str, Any], content: dict[str, Any] | None) -> str:
        if content:
            url = str(content.get("content_url") or "").strip()
            if url:
                return url

        content_id = str(item.get("content_id") or "").strip()
        content_type = str(item.get("content_type") or "").strip().lower()
        question_id = str(content.get("question_id") or "").strip() if content else ""

        if content_type == "answer" and question_id:
            return f"https://www.zhihu.com/question/{question_id}/answer/{content_id}"
        if content_type == "article" and content_id:
            return f"https://zhuanlan.zhihu.com/p/{content_id}"
        if content_type == "zvideo" and content_id:
            return f"https://www.zhihu.com/zvideo/{content_id}"
        if content_id:
            return f"https://www.zhihu.com/"
        return "https://www.zhihu.com/"

    def _resolve_title(self, item: dict[str, Any], content: dict[str, Any] | None) -> str | None:
        if content:
            title = clean_html_text(content.get("title"))
            if title:
                return title
            desc = clean_html_text(content.get("desc"))
            if desc:
                return desc[:120]
        return None

    def parse(self, raw_item: Any) -> CommentRecord | None:
        if not isinstance(raw_item, dict):
            return None

        crawl_time = raw_item.get("crawl_time")
        item = raw_item.get("item") if isinstance(raw_item.get("item"), dict) else raw_item
        if not isinstance(item, dict):
            return None
        if not isinstance(crawl_time, datetime):
            crawl_time = datetime.now()

        content = clean_html_text(item.get("content"))
        if not content:
            return None

        content_id = str(item.get("content_id") or "").strip()
        parent_content = self.content_index.get(content_id) if content_id else None

        return CommentRecord(
            platform="zhihu",
            content=content,
            source_url=self._build_content_url(item, parent_content),
            crawl_time=crawl_time,
            title=self._resolve_title(item, parent_content),
            author=clean_html_text(item.get("user_nickname")) or None,
            author_id=str(item.get("user_id") or "").strip() or None,
            comment_id=str(item.get("comment_id") or "").strip() or None,
            publish_time=parse_timestamp(item.get("publish_time")),
            like_count=coerce_int(item.get("like_count")),
            reply_count=coerce_int(item.get("sub_comment_count")),
            keywords=[self.keyword],
            raw_data={
                "keyword": self.keyword,
                "source_item": item,
                "parent_content": parent_content,
            },
        )
