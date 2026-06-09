"""解析模块入口：负责把原始接口数据转换为统一的评论结构。"""

from .base import BaseParser
from .hackernews import HackerNewsCommentParser

__all__ = ["BaseParser", "HackerNewsCommentParser"]
