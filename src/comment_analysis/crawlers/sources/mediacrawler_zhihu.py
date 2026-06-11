"""MediaCrawler 知乎采集器。"""

from __future__ import annotations

from typing import Any

from comment_analysis.parsers import ZhihuCommentParser
from comment_analysis.parsers.base import BaseParser

from .mediacrawler_base import MediaCrawlerBridgeCrawler


class MediaCrawlerZhihuCrawler(MediaCrawlerBridgeCrawler):
    platform_name = "zhihu"

    def _build_parser(self, content_index: dict[str, dict[str, Any]]) -> BaseParser:
        return ZhihuCommentParser(keyword=self.keyword, content_index=content_index)
