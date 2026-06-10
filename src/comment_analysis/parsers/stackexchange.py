"""Stack Exchange 评论解析器：把原始接口数据转换成标准评论对象。"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from html import unescape
from typing import Any

from comment_analysis.models import CommentRecord
from comment_analysis.parsers.base import BaseParser


class StackExchangeCommentParser(BaseParser):
    """负责解析 Stack Exchange 站点上的单条评论。"""

    def __init__(self, keyword: str, search_query: str, site: str = "politics") -> None:
        self.keyword = keyword.strip() or "美以伊战争"
        self.search_query = search_query.strip() or self.keyword
        self.site = site.strip() or "politics"

    def _clean_text(self, content: str | None) -> str:
        """去掉 HTML 标签并清理多余空白。"""
        if not content:
            return ""
        text = re.sub(r"<[^>]+>", " ", content)
        text = unescape(text)
        return " ".join(text.split())

    def _to_datetime(self, value: Any) -> datetime | None:
        """把时间戳或时间字符串转成带时区的 datetime。"""
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=timezone.utc)

        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _build_source_url(self, question: dict[str, Any], comment: dict[str, Any]) -> str:
        """优先返回带评论锚点的问题页面链接。"""
        question_link = str(question.get("link") or "").strip()
        question_id = str(question.get("question_id") or comment.get("post_id") or "").strip()
        comment_id = str(comment.get("comment_id") or "").strip()
        if question_link and question_id and comment_id:
            return f"{question_link}#comment{comment_id}_{question_id}"
        if question_link:
            return question_link
        if question_id:
            return f"https://{self.site}.stackexchange.com/questions/{question_id}"
        return f"https://{self.site}.stackexchange.com/"

    def parse(self, raw_item: Any) -> CommentRecord | None:
        """把单条评论与对应问题信息解析成标准评论对象。"""
        if not isinstance(raw_item, dict):
            return None

        question = raw_item.get("question")
        comment = raw_item.get("comment")
        crawl_time = raw_item.get("crawl_time")
        if not isinstance(question, dict) or not isinstance(comment, dict):
            return None
        if not isinstance(crawl_time, datetime):
            crawl_time = datetime.now(timezone.utc)

        body = self._clean_text(str(comment.get("body") or ""))
        if not body:
            return None

        owner = comment.get("owner")
        owner_dict = owner if isinstance(owner, dict) else {}
        title = self._clean_text(str(question.get("title") or "").strip()) or None
        comment_id = str(comment.get("comment_id") or "").strip() or None
        author = str(owner_dict.get("display_name") or "").strip() or None
        author_id = (
            str(owner_dict.get("user_id") or owner_dict.get("account_id") or "").strip() or None
        )

        return CommentRecord(
            platform="stackexchange",
            content=body,
            source_url=self._build_source_url(question, comment),
            crawl_time=crawl_time,
            title=title,
            author=author,
            author_id=author_id,
            comment_id=comment_id,
            publish_time=self._to_datetime(comment.get("creation_date")),
            like_count=comment.get("score"),
            raw_data={
                "keyword": self.keyword,
                "search_query": self.search_query,
                "site": self.site,
                "question_item": question,
                "comment_item": comment,
            },
        )
