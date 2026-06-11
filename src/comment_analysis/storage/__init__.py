"""存储模块入口：负责把结构化数据保存到本地文件。"""

from .repository import (
    BaseRepository,
    CsvFileRepository,
    JsonFileRepository,
    MemoryRepository,
    build_local_repository,
    build_repository,
)
from .raw import RawFileRepository
from .sqlite import SqliteCommentRepository

__all__ = [
    "BaseRepository",
    "CsvFileRepository",
    "JsonFileRepository",
    "MemoryRepository",
    "RawFileRepository",
    "SqliteCommentRepository",
    "build_local_repository",
    "build_repository",
]
