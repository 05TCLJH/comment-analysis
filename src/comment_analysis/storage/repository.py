"""存储模块：统一封装本地文件写入逻辑。"""

from __future__ import annotations

from abc import ABC, abstractmethod
import csv
import json
from pathlib import Path
from typing import Iterable

from comment_analysis.models.comment_record import CommentRecord


class BaseRepository(ABC):
    """数据存储仓库基类。"""

    @abstractmethod
    def save_many(
        self,
        records: Iterable[CommentRecord],
        *,
        job_id: str | None = None,
    ) -> int:
        """批量保存评论数据，返回新插入条数。"""
        raise NotImplementedError


class MemoryRepository(BaseRepository):
    """临时内存仓库，适合开发阶段调试。"""

    def __init__(self) -> None:
        self.records: list[CommentRecord] = []

    def save_many(
        self,
        records: Iterable[CommentRecord],
        *,
        job_id: str | None = None,
    ) -> int:
        items = list(records)
        self.records.extend(items)
        return len(items)


class JsonFileRepository(BaseRepository):
    """把评论数据保存为单个 JSON 文件。"""

    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path

    def save_many(
        self,
        records: Iterable[CommentRecord],
        *,
        job_id: str | None = None,
    ) -> int:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [record.to_dict() for record in records]
        self.output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return len(payload)


class CsvFileRepository(BaseRepository):
    """把评论数据保存为单个 CSV 文件。"""

    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path

    def save_many(
        self,
        records: Iterable[CommentRecord],
        *,
        job_id: str | None = None,
    ) -> int:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [self._serialize_row(record.to_dict()) for record in records]

        fieldnames = self._collect_fieldnames(payload)
        with self.output_path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(payload)
        return len(payload)

    def _serialize_row(self, row: dict[str, object]) -> dict[str, object]:
        """把复杂字段转换成适合写入 CSV 的字符串。"""
        serialized_row: dict[str, object] = {}
        for field_name, value in row.items():
            if isinstance(value, (dict, list)):
                serialized_row[field_name] = json.dumps(value, ensure_ascii=False)
            else:
                serialized_row[field_name] = value
        return serialized_row

    def _collect_fieldnames(self, rows: list[dict[str, object]]) -> list[str]:
        """收集 CSV 表头，尽量保持字段顺序稳定。"""
        if not rows:
            return [
                "platform",
                "content",
                "source_url",
                "crawl_time",
                "title",
                "author",
                "author_id",
                "comment_id",
                "publish_time",
                "like_count",
                "reply_count",
                "sentiment_label",
                "keywords",
                "raw_data",
            ]

        fieldnames: list[str] = []
        seen_fields: set[str] = set()
        for row in rows:
            for field_name in row.keys():
                if field_name in seen_fields:
                    continue
                seen_fields.add(field_name)
                fieldnames.append(field_name)
        return fieldnames


def build_local_repository(output_path: Path, output_format: str) -> BaseRepository:
    """按输出格式创建本地文件存储仓库。"""
    normalized_format = output_format.strip().lower()
    if normalized_format == "json":
        return JsonFileRepository(output_path)
    if normalized_format == "csv":
        return CsvFileRepository(output_path)
    raise ValueError(f"不支持的输出格式：{output_format}")


def build_repository(
    *,
    backend: str = "sqlite",
    database_url: str | None = None,
    output_path: Path | None = None,
    output_format: str = "json",
) -> BaseRepository:
    """按后端类型创建存储仓库，默认 SQLite。"""
    normalized = backend.strip().lower()
    if normalized == "sqlite":
        from comment_analysis.config.settings import settings
        from comment_analysis.storage.sqlite import SqliteCommentRepository

        url = database_url or settings.database_url
        if not url:
            raise ValueError("sqlite 后端需要 DATABASE_URL")
        return SqliteCommentRepository(url)
    if normalized == "json":
        if output_path is None:
            raise ValueError("json 后端需要 output_path")
        return JsonFileRepository(output_path)
    if normalized == "csv":
        if output_path is None:
            raise ValueError("csv 后端需要 output_path")
        return CsvFileRepository(output_path)
    raise ValueError(f"不支持的存储后端：{backend}")
