"""MediaCrawler 微博采集器。"""

from __future__ import annotations

from typing import Any

from comment_analysis.parsers import WeiboCommentParser
from comment_analysis.parsers.base import BaseParser

from .mediacrawler_base import MediaCrawlerBridgeCrawler


class MediaCrawlerWeiboCrawler(MediaCrawlerBridgeCrawler):
    platform_name = "weibo"

    def _build_parser(self, content_index: dict[str, dict[str, Any]]) -> BaseParser:
        return WeiboCommentParser(keyword=self.keyword, content_index=content_index)
