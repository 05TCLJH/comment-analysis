"""SQLite 主存储：评论表 + 采集任务表。"""

from __future__ import annotations

import json
from typing import Iterable

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    select,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from comment_analysis.models import CommentRecord, CrawlJob


class Base(DeclarativeBase):
    pass


class CrawlJobRow(Base):
    __tablename__ = "crawl_jobs"

    job_id = Column(String(64), primary_key=True)
    keyword = Column(String(256), nullable=False)
    source = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    raw_count = Column(Integer, default=0)
    cleaned_count = Column(Integer, default=0)
    params_json = Column(Text, default="{}")


class CommentRow(Base):
    __tablename__ = "comments"
    __table_args__ = (UniqueConstraint("platform", "comment_id", name="uq_platform_comment"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(64), nullable=True, index=True)
    platform = Column(String(64), nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(Text, nullable=False)
    crawl_time = Column(DateTime, nullable=False)
    title = Column(String(512), nullable=True)
    author = Column(String(256), nullable=True)
    author_id = Column(String(128), nullable=True)
    comment_id = Column(String(128), nullable=True)
    publish_time = Column(DateTime, nullable=True)
    like_count = Column(Integer, nullable=True)
    reply_count = Column(Integer, nullable=True)
    sentiment_label = Column(String(32), nullable=True)
    keywords_json = Column(Text, default="[]")
    raw_data_json = Column(Text, default="{}")


class SqliteCommentRepository:
    def __init__(self, database_url: str) -> None:
        self.engine = create_engine(database_url, future=True)
        Base.metadata.create_all(self.engine)
        self._Session = sessionmaker(bind=self.engine, future=True)

    def close(self) -> None:
        self.engine.dispose()

    def create_crawl_job(self, job: CrawlJob) -> None:
        with self._Session() as session:
            session.merge(
                CrawlJobRow(
                    job_id=job.job_id,
                    keyword=job.keyword,
                    source=job.source,
                    status=job.status,
                    started_at=job.started_at,
                    finished_at=job.finished_at,
                    raw_count=job.raw_count,
                    cleaned_count=job.cleaned_count,
                    params_json=json.dumps(job.params or {}, ensure_ascii=False),
                )
            )
            session.commit()

    def update_crawl_job(self, job: CrawlJob) -> None:
        self.create_crawl_job(job)

    def get_last_crawl_job_id(self) -> str | None:
        with self._Session() as session:
            row = session.execute(
                select(CrawlJobRow.job_id).order_by(CrawlJobRow.started_at.desc()).limit(1)
            ).scalar_one_or_none()
            return row

    def save_many(
        self,
        records: Iterable[CommentRecord],
        *,
        job_id: str | None = None,
    ) -> int:
        inserted = 0
        with self._Session() as session:
            for record in records:
                if not record.comment_id:
                    continue
                exists = session.execute(
                    select(CommentRow.id).where(
                        CommentRow.platform == record.platform,
                        CommentRow.comment_id == record.comment_id,
                    )
                ).scalar_one_or_none()
                if exists is not None:
                    continue
                session.add(self._to_row(record, job_id))
                inserted += 1
            session.commit()
        return inserted

    def fetch_comments(self, *, job_id: str | None = None) -> list[CommentRecord]:
        with self._Session() as session:
            stmt = select(CommentRow)
            if job_id:
                stmt = stmt.where(CommentRow.job_id == job_id)
            rows = session.execute(stmt).scalars().all()
            return [self._from_row(row) for row in rows]

    def _to_row(self, record: CommentRecord, job_id: str | None) -> CommentRow:
        data = record.to_dict()
        return CommentRow(
            job_id=job_id,
            platform=data["platform"],
            content=data["content"],
            source_url=data["source_url"],
            crawl_time=record.crawl_time,
            title=data.get("title"),
            author=data.get("author"),
            author_id=data.get("author_id"),
            comment_id=data.get("comment_id"),
            publish_time=record.publish_time,
            like_count=data.get("like_count"),
            reply_count=data.get("reply_count"),
            sentiment_label=data.get("sentiment_label"),
            keywords_json=json.dumps(data.get("keywords") or [], ensure_ascii=False),
            raw_data_json=json.dumps(data.get("raw_data") or {}, ensure_ascii=False),
        )

    def _from_row(self, row: CommentRow) -> CommentRecord:
        return CommentRecord.from_dict(
            {
                "platform": row.platform,
                "content": row.content,
                "source_url": row.source_url,
                "crawl_time": row.crawl_time,
                "title": row.title,
                "author": row.author,
                "author_id": row.author_id,
                "comment_id": row.comment_id,
                "publish_time": row.publish_time,
                "like_count": row.like_count,
                "reply_count": row.reply_count,
                "sentiment_label": row.sentiment_label,
                "keywords": json.loads(row.keywords_json or "[]"),
                "raw_data": json.loads(row.raw_data_json or "{}"),
            }
        )
