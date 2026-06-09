"""来源适配模块入口：集中放置各个具体数据源的爬虫实现。"""

from .hackernews import HackerNewsCommentCrawler

__all__ = ["HackerNewsCommentCrawler"]
