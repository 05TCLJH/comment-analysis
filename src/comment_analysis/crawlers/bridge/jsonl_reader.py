"""MediaCrawler JSONL 输出读取。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonlCommentReader:
    """读取 MediaCrawler search 模式产出的 comments / contents JSONL。"""

    def __init__(self, save_path: Path) -> None:
        self.save_path = Path(save_path)

    def _jsonl_dirs(self) -> list[Path]:
        """MediaCrawler 可能在 save_path 下再嵌套一层 platform 目录。"""
        candidates: list[Path] = []
        direct = self.save_path / "jsonl"
        if direct.is_dir():
            candidates.append(direct)
        for nested in sorted(self.save_path.rglob("jsonl")):
            if nested.is_dir() and nested not in candidates:
                candidates.append(nested)
        return candidates

    def _read_jsonl_files(self, pattern: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen_files: set[Path] = set()
        for jsonl_dir in self._jsonl_dirs():
            for file_path in sorted(jsonl_dir.glob(pattern)):
                if file_path in seen_files:
                    continue
                seen_files.add(file_path)
                with file_path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        text = line.strip()
                        if not text:
                            continue
                        payload = json.loads(text)
                        if isinstance(payload, dict):
                            rows.append(payload)
        return rows

    def read_comments(self) -> list[dict[str, Any]]:
        """读取 search_comments_*.jsonl。"""
        return self._read_jsonl_files("search_comments_*.jsonl")

    def read_contents(self) -> list[dict[str, Any]]:
        """读取 search_contents_*.jsonl，供 title / URL 关联。"""
        return self._read_jsonl_files("search_contents_*.jsonl")

    def build_content_index(self) -> dict[str, dict[str, Any]]:
        """按 content_id / note_id 建立内容索引。"""
        index: dict[str, dict[str, Any]] = {}
        for item in self.read_contents():
            for key in ("content_id", "note_id", "id"):
                value = item.get(key)
                if value is not None and str(value).strip():
                    index[str(value).strip()] = item
        return index
