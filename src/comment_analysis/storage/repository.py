"""存储模块：统一封装数据写入和读取逻辑。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from comment_analysis.models.comment_record import CommentRecord


class BaseRepository(ABC):
    """数据存储仓库基类。"""

    @abstractmethod
    def save_many(self, records: Iterable[CommentRecord]) -> None:
        """批量保存评论数据。"""
        raise NotImplementedError


class MemoryRepository(BaseRepository):
    """临时内存仓库，适合开发阶段调试。"""

    def __init__(self) -> None:
        self.records: list[CommentRecord] = []

    def save_many(self, records: Iterable[CommentRecord]) -> None:
        self.records.extend(records)