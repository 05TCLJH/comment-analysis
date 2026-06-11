"""MediaCrawler Bridge 平台采集器基类。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from comment_analysis.config.settings import settings
from comment_analysis.crawlers.base import BaseCrawler
from comment_analysis.crawlers.bridge import JsonlCommentReader, MediaCrawlerRunner
from comment_analysis.models import CommentRecord
from comment_analysis.parsers.base import BaseParser


class MediaCrawlerBridgeCrawler(BaseCrawler):
    """通过 MediaCrawler 子进程抓取评论并解析为 CommentRecord。"""

    platform_name: str = "tieba"

    def __init__(
        self,
        *,
        keyword: str,
        max_records: int = 20,
        job_id: str,
        raw_dir: Path | None = None,
        parser: BaseParser | None = None,
        runner: MediaCrawlerRunner | None = None,
        max_comments_per_note: int | None = None,
    ) -> None:
        self.keyword = keyword.strip() or "美以伊战争"
        self.max_records = max(1, min(max_records, 100))
        self.job_id = job_id.strip()
        if not self.job_id:
            raise ValueError("job_id 不能为空")
        self.raw_dir = raw_dir or settings.raw_dir
        self.parser = parser
        self.runner = runner or MediaCrawlerRunner(
            timeout_seconds=settings.mediacrawler_timeout_seconds
        )
        self.max_comments_per_note = max_comments_per_note or settings.mediacrawler_max_comments_per_note

    def _save_path(self) -> Path:
        return self.raw_dir / "mediacrawler" / self.job_id / self.platform_name

    def _build_parser(self, content_index: dict[str, dict[str, Any]]) -> BaseParser:
        raise NotImplementedError

    def crawl_with_raw(self) -> tuple[dict[str, Any], list[CommentRecord]]:
        save_path = self._save_path()
        run_result = self.runner.run(
            platform=self.platform_name,
            keyword=self.keyword,
            save_path=save_path,
            max_notes=self.max_records,
            max_comments_per_note=self.max_comments_per_note,
        )

        reader = JsonlCommentReader(save_path)
        content_index = reader.build_content_index()
        parser = self.parser or self._build_parser(content_index)
        crawl_time = datetime.now()
        comment_rows = reader.read_comments()
        parse_items = [
            {"item": row, "crawl_time": crawl_time}
            for row in comment_rows
        ]
        records = parser.parse_many(parse_items)

        raw_payload = {
            "mediacrawler": {
                "platform": self.platform_name,
                "save_path": str(save_path),
                "returncode": run_result.returncode,
                "stdout_tail": run_result.stdout[-4000:],
                "stderr_tail": run_result.stderr[-4000:],
            },
            "jsonl_dir": str(save_path / "jsonl"),
            "line_count": len(comment_rows),
            "content_count": len(content_index),
            "record_count": len(records),
        }
        return raw_payload, records

    def crawl(self) -> list[CommentRecord]:
        _, records = self.crawl_with_raw()
        return records
