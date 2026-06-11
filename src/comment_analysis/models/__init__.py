"""评论分析流程使用的数据模型入口。"""

from .comment_record import CommentRecord
from .crawl_job import CrawlJob

__all__ = ["CommentRecord", "CrawlJob"]
