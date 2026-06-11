"""采集任务模型。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping


def _parse_dt(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


@dataclass(slots=True)
class CrawlJob:
    job_id: str
    keyword: str
    source: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    raw_count: int = 0
    cleaned_count: int = 0
    params: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "keyword": self.keyword,
            "source": self.source,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "raw_count": self.raw_count,
            "cleaned_count": self.cleaned_count,
            "params": self.params or {},
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CrawlJob":
        return cls(
            job_id=str(data["job_id"]),
            keyword=str(data["keyword"]),
            source=str(data["source"]),
            status=str(data["status"]),
            started_at=_parse_dt(data["started_at"]) or datetime.now(),
            finished_at=_parse_dt(data.get("finished_at")),
            raw_count=int(data.get("raw_count", 0)),
            cleaned_count=int(data.get("cleaned_count", 0)),
            params=dict(data.get("params") or {}),
        )
