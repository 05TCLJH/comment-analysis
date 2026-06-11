"""流程编排模块：负责串联采集、清洗、存储和分析流程。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from comment_analysis.analysis import assign_keywords, assign_sentiment, build_analysis_report
from comment_analysis.config.settings import settings
from comment_analysis.crawlers.base import BaseCrawler
from comment_analysis.entry.clean import clean_records
from comment_analysis.entry.crawl import collect_with_raw
from comment_analysis.models import CrawlJob
from comment_analysis.storage.raw import RawFileRepository
from comment_analysis.storage.repository import BaseRepository, build_repository
from comment_analysis.visualization import write_analysis_report


class PipelineOrchestrator:
    """流程编排器：把采集和保存串起来。"""

    def __init__(self, crawler: BaseCrawler, repository: BaseRepository) -> None:
        self.crawler = crawler
        self.repository = repository

    def run_crawl(self) -> None:
        """运行采集流程，并把结果保存到存储层。"""
        records = self.crawler.crawl()
        self.repository.save_many(records)

    def close(self) -> None:
        """关闭采集器等资源，避免连接或句柄泄漏。"""
        self.crawler.close()


class FullPipeline:
    """全链路编排：crawl → raw → clean → db → analyze → html。"""

    def __init__(
        self,
        *,
        keyword: str,
        max_records: int,
        source: str,
        database_url: str | None = None,
        raw_dir: Path | None = None,
        results_dir: Path | None = None,
        storage_backend: str = "sqlite",
    ) -> None:
        normalized_backend = storage_backend.strip().lower()
        if normalized_backend != "sqlite":
            raise ValueError(
                f"FullPipeline 仅支持 sqlite 存储后端，当前为：{storage_backend}"
            )

        self.keyword = keyword
        self.max_records = max_records
        self.source = source
        self.database_url = database_url or settings.database_url
        self.raw_dir = raw_dir or settings.raw_dir
        self.results_dir = results_dir or settings.results_dir
        self.storage_backend = normalized_backend
        self._repo = build_repository(
            backend=self.storage_backend,
            database_url=self.database_url,
        )
        self._raw_repo = RawFileRepository(self.raw_dir)

    def run(self, *, top_n: int = 20, per_record_top_n: int = 5) -> dict[str, object]:
        job_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
        started_at = datetime.now()

        job = CrawlJob(
            job_id=job_id,
            keyword=self.keyword,
            source=self.source,
            status="running",
            started_at=started_at,
            params={"limit": self.max_records},
        )

        try:
            if hasattr(self._repo, "create_crawl_job"):
                self._repo.create_crawl_job(job)

            bundles = collect_with_raw(
                keyword=self.keyword,
                max_records=self.max_records,
                source=self.source,
            )

            raw_count = 0
            all_records = []
            for bundle in bundles:
                platform = str(bundle["platform"])
                self._raw_repo.save_payload(
                    platform=platform,
                    job_id=job_id,
                    payload=dict(bundle["raw_payload"]),
                )
                records = bundle["records"]
                raw_count += len(records)
                all_records.extend(records)

            cleaned = clean_records(all_records)
            inserted = self._repo.save_many(cleaned, job_id=job_id)

            enriched = assign_sentiment(assign_keywords(cleaned, top_n=per_record_top_n))
            report = build_analysis_report(enriched, top_n=top_n)

            self.results_dir.mkdir(parents=True, exist_ok=True)
            report_json_path = self.results_dir / f"job_{job_id}_analysis.json"
            report_json_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            report_html_path = write_analysis_report(
                report,
                self.results_dir,
                report_json_path.stem,
            )

            finished_job = CrawlJob(
                job_id=job_id,
                keyword=self.keyword,
                source=self.source,
                status="completed",
                started_at=started_at,
                finished_at=datetime.now(),
                raw_count=raw_count,
                cleaned_count=len(cleaned),
                params=job.params,
            )
            if hasattr(self._repo, "update_crawl_job"):
                self._repo.update_crawl_job(finished_job)

            return {
                "job_id": job_id,
                "database_url": self.database_url,
                "raw_count": raw_count,
                "cleaned_count": len(cleaned),
                "inserted_count": inserted,
                "report_json_path": report_json_path,
                "report_html_path": report_html_path,
            }
        except Exception:
            failed_job = CrawlJob(
                job_id=job_id,
                keyword=self.keyword,
                source=self.source,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(),
                params=job.params,
            )
            if hasattr(self._repo, "update_crawl_job"):
                self._repo.update_crawl_job(failed_job)
            raise

    def close(self) -> None:
        if hasattr(self._repo, "close"):
            self._repo.close()
