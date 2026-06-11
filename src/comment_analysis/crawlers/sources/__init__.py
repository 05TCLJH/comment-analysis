"""数据源适配器入口。"""

from .hackernews import HackerNewsCommentCrawler
from .mediacrawler_tieba import MediaCrawlerTiebaCrawler
from .mediacrawler_weibo import MediaCrawlerWeiboCrawler
from .mediacrawler_zhihu import MediaCrawlerZhihuCrawler
from .stackexchange import StackExchangeCommentCrawler

__all__ = [
    "HackerNewsCommentCrawler",
    "StackExchangeCommentCrawler",
    "MediaCrawlerTiebaCrawler",
    "MediaCrawlerZhihuCrawler",
    "MediaCrawlerWeiboCrawler",
]
