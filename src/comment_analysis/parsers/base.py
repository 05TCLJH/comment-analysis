"""解析器基类模块：定义不同页面结构的通用解析入口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from comment_analysis.models.comment_record import CommentRecord


class BaseParser(ABC):
    """所有解析器都应该继承这个基类。"""

    @abstractmethod
    def parse(self, raw_item: Any) -> CommentRecord:
        """把一条原始数据解析成标准评论对象。"""
        raise NotImplementedError
