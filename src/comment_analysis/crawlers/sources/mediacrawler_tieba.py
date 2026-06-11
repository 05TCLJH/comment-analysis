"""MediaCrawler 贴吧采集器。"""

from __future__ import annotations

from typing import Any

from comment_analysis.parsers import TiebaCommentParser
from comment_analysis.parsers.base import BaseParser

from .mediacrawler_base import MediaCrawlerBridgeCrawler


class MediaCrawlerTiebaCrawler(MediaCrawlerBridgeCrawler):
    platform_name = "tieba"

    def _build_parser(self, content_index: dict[str, dict[str, Any]]) -> BaseParser:
        return TiebaCommentParser(keyword=self.keyword, content_index=content_index)
