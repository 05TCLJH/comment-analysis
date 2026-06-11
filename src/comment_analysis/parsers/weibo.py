"""微博 JSONL 解析器。"""

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


class WeiboCommentParser(BaseParser):
    """解析 MediaCrawler 微博 comments JSONL。"""

    def __init__(self, keyword: str, content_index: dict[str, dict[str, Any]] | None = None) -> None:
        self.keyword = keyword.strip() or "美以伊战争"
        self.content_index = content_index or {}

    def _resolve_title(self, note_id: str) -> str | None:
        if not note_id:
            return None
        content = self.content_index.get(note_id)
        if not content:
            return None
        title = clean_html_text(content.get("content"))
        if title:
            return title[:120]
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

        note_id = str(item.get("note_id") or "").strip()
        source_url = f"https://m.weibo.cn/detail/{note_id}" if note_id else "https://m.weibo.cn/"

        publish_time = parse_timestamp(item.get("create_date_time"))
        if publish_time is None:
            publish_time = parse_timestamp(item.get("create_time"))

        return CommentRecord(
            platform="weibo",
            content=content,
            source_url=source_url,
            crawl_time=crawl_time,
            title=self._resolve_title(note_id),
            author=clean_html_text(item.get("nickname")) or None,
            author_id=str(item.get("user_id") or "").strip() or None,
            comment_id=str(item.get("comment_id") or "").strip() or None,
            publish_time=publish_time,
            like_count=coerce_int(item.get("comment_like_count")),
            reply_count=coerce_int(item.get("sub_comment_count")),
            keywords=[self.keyword],
            raw_data={
                "keyword": self.keyword,
                "source_item": item,
            },
        )
