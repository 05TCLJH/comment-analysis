"""爬虫基类模块：统一不同来源采集器的接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from comment_analysis.models.comment_record import CommentRecord


class BaseCrawler(ABC):
    """所有平台爬虫都应该继承这个基类。"""

    # 平台名称，由子类自行定义
    platform_name: str = "base"

    @abstractmethod
    def crawl(self) -> Iterable[CommentRecord]:
        """执行采集流程，返回评论记录迭代器。"""
        raise NotImplementedError

    def close(self) -> None:
        """释放资源，子类可以按需重写。"""
        return None
