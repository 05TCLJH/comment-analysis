"""百度贴吧 JSONL 解析器。"""

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


class TiebaCommentParser(BaseParser):
    """解析 MediaCrawler 贴吧 comments JSONL。"""

    def __init__(self, keyword: str, content_index: dict[str, dict[str, Any]] | None = None) -> None:
        self.keyword = keyword.strip() or "美以伊战争"
        self.content_index = content_index or {}

    def _resolve_title(self, item: dict[str, Any]) -> str | None:
        note_id = str(item.get("note_id") or "").strip()
        content = self.content_index.get(note_id) if note_id else None
        if content:
            title = clean_html_text(content.get("title"))
            if title:
                return title
        tieba_name = clean_html_text(item.get("tieba_name"))
        return tieba_name or None

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

        source_url = str(item.get("note_url") or "").strip()
        if not source_url:
            note_id = str(item.get("note_id") or "").strip()
            if note_id:
                source_url = f"https://tieba.baidu.com/p/{note_id}"

        return CommentRecord(
            platform="tieba",
            content=content,
            source_url=source_url or "https://tieba.baidu.com/",
            crawl_time=crawl_time,
            title=self._resolve_title(item),
            author=clean_html_text(item.get("user_nickname")) or None,
            comment_id=str(item.get("comment_id") or "").strip() or None,
            publish_time=parse_timestamp(item.get("publish_time")),
            reply_count=coerce_int(item.get("sub_comment_count")),
            keywords=[self.keyword],
            raw_data={
                "keyword": self.keyword,
                "source_item": item,
            },
        )
