"""流程编排模块：负责串联采集、清洗、存储和分析流程。"""

from __future__ import annotations

from comment_analysis.crawlers.base import BaseCrawler
from comment_analysis.storage.repository import BaseRepository


class PipelineOrchestrator:
    """流程编排器。

    这个类的作用是把各个独立模块串起来，
    方便后面一键执行采集和保存流程。
    """

    def __init__(self, crawler: BaseCrawler, repository: BaseRepository) -> None:
        self.crawler = crawler
        self.repository = repository

    def run_crawl(self) -> None:
        """运行采集流程，并把结果保存到仓库中。"""
        records = self.crawler.crawl()
        self.repository.save_many(records)

    def close(self) -> None:
        """关闭爬虫等资源，防止连接或句柄泄漏。"""
        self.crawler.close()