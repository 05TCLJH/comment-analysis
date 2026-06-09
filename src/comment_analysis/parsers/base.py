"""解析器基类模块：定义不同数据源的通用解析入口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from comment_analysis.models.comment_record import CommentRecord


class BaseParser(ABC):
    """所有解析器都应该继承这个基类。"""

    @abstractmethod
    def parse(self, raw_item: Any) -> CommentRecord | None:
        """把一条原始数据解析成标准评论对象。"""
        raise NotImplementedError

    def parse_many(self, raw_items: Iterable[Any]) -> list[CommentRecord]:
        """批量解析原始数据，并自动跳过空结果。"""
        records: list[CommentRecord] = []
        for raw_item in raw_items:
            record = self.parse(raw_item)
            if record is not None:
                records.append(record)
        return records
