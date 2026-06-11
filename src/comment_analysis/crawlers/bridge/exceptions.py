"""MediaCrawler Bridge 异常定义。"""

from __future__ import annotations


class MediaCrawlerError(RuntimeError):
    """MediaCrawler 子进程或输出解析失败。"""
