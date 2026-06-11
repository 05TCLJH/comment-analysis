# P0 完整链路 + SQLite + Raw 落盘 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 一条命令完成「采集 → raw 落盘 → 清洗 → SQLite 入库 → 分析 → HTML」，分析可从数据库按 `job_id` 读数，不再依赖手动找最新 JSON。

**Architecture:** 在现有 `run_all` + `analyze` 能力上增量扩展：新增 `CrawlJob` 模型与 SQLAlchemy SQLite 层作为主存储；`RawFileRepository` 保存各平台 API 原始响应；`FullPipeline` 编排器串联 crawl/raw/clean/db/analyze；`entry/pipeline.py` 作为统一 CLI 入口。文件 JSON/CSV 保留为可选导出，默认后端为 `sqlite`。

**Tech Stack:** Python 3.12、stdlib `unittest`、`sqlalchemy`、`python-dotenv`、现有 `CommentRecord` / `assign_keywords` / `build_analysis_report` / ECharts HTML。

**范围说明：** 本计划仅覆盖 `PROJECT_BACKLOG.md` 第六节 **P0-1～P0-8**；双语 jieba/NLTK/VADER（P1）不在本计划内，pipeline 复用现有规则化分析即可。

**建议执行环境：** 在独立 git worktree 中实施（`superpowers:using-git-worktrees`）。

---

## 文件结构总览

| 文件 | 职责 |
|------|------|
| `requirements.txt` | 取消注释，写入 `sqlalchemy`、`python-dotenv` |
| `src/comment_analysis/config/settings.py` | 加载 `.env`；默认 `DATABASE_URL` 指向 `data/comment_analysis.db` |
| `src/comment_analysis/models/crawl_job.py` | `CrawlJob` 数据类 |
| `src/comment_analysis/models/__init__.py` | 导出 `CrawlJob` |
| `src/comment_analysis/storage/sqlite.py` | SQLAlchemy 引擎、表、`SqliteCommentRepository` |
| `src/comment_analysis/storage/raw.py` | `RawFileRepository`：写 `data/raw/{platform}/{job_id}.json` |
| `src/comment_analysis/storage/repository.py` | `build_repository()` 工厂；`save_many` 增加可选 `job_id` |
| `src/comment_analysis/storage/__init__.py` | 导出新符号 |
| `src/comment_analysis/entry/crawl.py` | 新增 `collect_with_raw()`，返回 raw payload + records |
| `src/comment_analysis/pipeline/orchestrator.py` | 扩展为 `FullPipeline`（crawl→raw→clean→db→analyze） |
| `src/comment_analysis/entry/pipeline.py` | **新增** 全链路 CLI |
| `src/comment_analysis/entry/analyze.py` | 支持 `--from-db` / `--job-id` / `--last-job` |
| `tests/test_sqlite_repository.py` | SQLite 去重、按 job 查询 |
| `tests/test_raw_repository.py` | Raw 落盘路径与内容 |
| `tests/test_pipeline_entry.py` | Mock 采集的端到端集成测试 |
| `tests/test_analyze_from_db.py` | 从 DB 读数再分析 |

---

## 任务依赖顺序

```text
Task 1 (dotenv/settings)
    → Task 2 (CrawlJob model)
    → Task 3 (SQLite repo + tests)
    → Task 4 (Raw repo + tests)
    → Task 5 (collect_with_raw)
    → Task 6 (build_repository factory)
    → Task 7 (FullPipeline orchestrator)
    → Task 8 (entry/pipeline.py)
    → Task 9 (analyze --from-db)
    → Task 10 (集成测试 + 手工验收)
```

---

### Task 1: 依赖与 `.env` 加载（P0-7）

**Files:**
- Modify: `requirements.txt`
- Modify: `src/comment_analysis/config/settings.py`
- Modify: `.env.example`
- Test: `tests/test_settings.py`（新建）

- [ ] **Step 1: Write the failing test**

```python
# tests/test_settings.py
"""配置测试：验证 dotenv 加载与默认 SQLite 路径。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class SettingsTest(unittest.TestCase):
    def test_default_database_url_points_to_sqlite_file(self) -> None:
        # 重新导入以获取默认配置
        import importlib
        import comment_analysis.config.settings as settings_module

        importlib.reload(settings_module)
        url = settings_module.settings.database_url
        self.assertTrue(url.startswith("sqlite:///"))
        self.assertIn("comment_analysis.db", url)

    def test_dotenv_overrides_database_url(self) -> None:
        import importlib
        import comment_analysis.config.settings as settings_module

        os.environ["DATABASE_URL"] = "sqlite:///tmp/test_override.db"
        try:
            importlib.reload(settings_module)
            self.assertEqual(
                settings_module.settings.database_url,
                "sqlite:///tmp/test_override.db",
            )
        finally:
            del os.environ["DATABASE_URL"]
            importlib.reload(settings_module)
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
cd D:\comment-analysis
$env:PYTHONPATH = "src"
python -m unittest tests.test_settings -v
```

Expected: FAIL — `database_url` 为空或不含 `comment_analysis.db`

- [ ] **Step 3: Write minimal implementation**

`requirements.txt` 改为：

```text
sqlalchemy>=2.0,<3.0
python-dotenv>=1.0,<2.0
```

`settings.py` 在文件顶部 `import os` 之后增加：

```python
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")
```

并将 `Settings.database_url` 默认值改为：

```python
database_url: str = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{(DATA_DIR / 'comment_analysis.db').as_posix()}",
)
```

`.env.example` 增加：

```text
DATABASE_URL=sqlite:///data/comment_analysis.db
STORAGE_BACKEND=sqlite
```

- [ ] **Step 4: Run test to verify it passes**

```powershell
pip install -r requirements.txt
python -m unittest tests.test_settings -v
```

Expected: PASS（2 tests）

- [ ] **Step 5: Commit**

```powershell
git add requirements.txt src/comment_analysis/config/settings.py .env.example tests/test_settings.py
git commit -m "feat: load dotenv and default SQLite DATABASE_URL"
```

---

### Task 2: CrawlJob 模型（P0-3 前半）

**Files:**
- Create: `src/comment_analysis/models/crawl_job.py`
- Modify: `src/comment_analysis/models/__init__.py`
- Test: `tests/test_crawl_job.py`（新建）

- [ ] **Step 1: Write the failing test**

```python
# tests/test_crawl_job.py
"""CrawlJob 模型测试。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.models import CrawlJob


class CrawlJobTest(unittest.TestCase):
    def test_from_dict_round_trip(self) -> None:
        job = CrawlJob(
            job_id="job-001",
            keyword="美以伊战争",
            source="all",
            status="completed",
            started_at=datetime(2026, 6, 11, 10, 0, 0),
            finished_at=datetime(2026, 6, 11, 10, 1, 0),
            raw_count=10,
            cleaned_count=8,
        )
        restored = CrawlJob.from_dict(job.to_dict())
        self.assertEqual(restored.job_id, "job-001")
        self.assertEqual(restored.cleaned_count, 8)
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m unittest tests.test_crawl_job -v
```

Expected: FAIL — `ImportError: cannot import name 'CrawlJob'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/comment_analysis/models/crawl_job.py
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
```

`models/__init__.py` 增加：

```python
from .crawl_job import CrawlJob
```

并在 `__all__` 中导出 `CrawlJob`。

- [ ] **Step 4: Run test to verify it passes**

```powershell
python -m unittest tests.test_crawl_job -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/comment_analysis/models/crawl_job.py src/comment_analysis/models/__init__.py tests/test_crawl_job.py
git commit -m "feat: add CrawlJob model for crawl task metadata"
```

---

### Task 3: SQLite Repository（P0-2 + P0-3）

**Files:**
- Create: `src/comment_analysis/storage/sqlite.py`
- Modify: `src/comment_analysis/storage/repository.py`（`save_many` 签名加 `job_id`）
- Modify: `src/comment_analysis/storage/__init__.py`
- Test: `tests/test_sqlite_repository.py`（新建）

- [ ] **Step 1: Write the failing test**

```python
# tests/test_sqlite_repository.py
"""SQLite 存储测试：去重、按 job 查询。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.models import CommentRecord, CrawlJob
from comment_analysis.storage.sqlite import SqliteCommentRepository


class SqliteRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.repo = SqliteCommentRepository(f"sqlite:///{self.db_path.as_posix()}")

    def tearDown(self) -> None:
        self.repo.close()
        self.temp_dir.cleanup()

    def _sample_record(self, comment_id: str) -> CommentRecord:
        return CommentRecord(
            platform="hackernews",
            content=f"comment {comment_id}",
            source_url=f"https://example.com/{comment_id}",
            crawl_time=datetime(2026, 6, 11, 10, 0, 0),
            comment_id=comment_id,
        )

    def test_save_many_dedupes_by_platform_and_comment_id(self) -> None:
        job = CrawlJob(
            job_id="job-a",
            keyword="test",
            source="hackernews",
            status="running",
            started_at=datetime(2026, 6, 11, 10, 0, 0),
        )
        self.repo.create_crawl_job(job)

        first = self.repo.save_many(
            [self._sample_record("c1"), self._sample_record("c2")],
            job_id="job-a",
        )
        second = self.repo.save_many(
            [self._sample_record("c1"), self._sample_record("c3")],
            job_id="job-a",
        )

        self.assertEqual(first, 2)
        self.assertEqual(second, 1)  # c1 重复，仅 c3 新增

        rows = self.repo.fetch_comments(job_id="job-a")
        self.assertEqual(len(rows), 3)

    def test_fetch_comments_without_job_returns_all(self) -> None:
        self.repo.save_many([self._sample_record("x1")], job_id="job-x")
        self.repo.save_many([self._sample_record("x2")], job_id="job-y")
        self.assertEqual(len(self.repo.fetch_comments()), 2)

    def test_get_last_crawl_job_id(self) -> None:
        for job_id in ("job-1", "job-2"):
            self.repo.create_crawl_job(
                CrawlJob(
                    job_id=job_id,
                    keyword="k",
                    source="all",
                    status="completed",
                    started_at=datetime(2026, 6, 11, 10, 0, 0),
                    finished_at=datetime(2026, 6, 11, 10, 1, 0),
                )
            )
        self.assertEqual(self.repo.get_last_crawl_job_id(), "job-2")
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m unittest tests.test_sqlite_repository -v
```

Expected: FAIL — `ModuleNotFoundError: storage.sqlite`

- [ ] **Step 3: Write minimal implementation**

`repository.py` 修改 `BaseRepository.save_many` 签名：

```python
@abstractmethod
def save_many(
    self,
    records: Iterable[CommentRecord],
    *,
    job_id: str | None = None,
) -> int:
    """批量保存评论数据，返回新插入条数。"""
```

`MemoryRepository` / `JsonFileRepository` / `CsvFileRepository` 的 `save_many` 增加 `job_id` 参数（忽略），返回 `len(list(records))` 或实际写入条数。

`sqlite.py` 核心结构：

```python
# src/comment_analysis/storage/sqlite.py
"""SQLite 主存储：评论表 + 采集任务表。"""

from __future__ import annotations

import json
from datetime import datetime
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
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

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
```

- [ ] **Step 4: Run test to verify it passes**

```powershell
python -m unittest tests.test_sqlite_repository -v
```

Expected: PASS（3 tests）

- [ ] **Step 5: Commit**

```powershell
git add src/comment_analysis/storage/sqlite.py src/comment_analysis/storage/repository.py src/comment_analysis/storage/__init__.py tests/test_sqlite_repository.py
git commit -m "feat: add SQLite repository with crawl_jobs and comment dedup"
```

---

### Task 4: Raw 落盘（P0-4）

**Files:**
- Create: `src/comment_analysis/storage/raw.py`
- Modify: `src/comment_analysis/storage/__init__.py`
- Test: `tests/test_raw_repository.py`（新建）

- [ ] **Step 1: Write the failing test**

```python
# tests/test_raw_repository.py
"""Raw 落盘测试。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.storage.raw import RawFileRepository


class RawRepositoryTest(unittest.TestCase):
    def test_save_payload_writes_expected_path(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo = RawFileRepository(Path(temp_dir))
            path = repo.save_payload(
                platform="hackernews",
                job_id="job-abc",
                payload={"hits": [{"objectID": "1"}]},
            )
            self.assertEqual(path, Path(temp_dir) / "hackernews" / "job-abc.json")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["hits"][0]["objectID"], "1")
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m unittest tests.test_raw_repository -v
```

Expected: FAIL — module not found

- [ ] **Step 3: Write minimal implementation**

```python
# src/comment_analysis/storage/raw.py
"""原始 API 响应落盘。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RawFileRepository:
    def __init__(self, raw_dir: Path) -> None:
        self.raw_dir = raw_dir

    def save_payload(
        self,
        *,
        platform: str,
        job_id: str,
        payload: dict[str, Any],
    ) -> Path:
        target_dir = self.raw_dir / platform.strip().lower()
        target_dir.mkdir(parents=True, exist_ok=True)
        output_path = target_dir / f"{job_id}.json"
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return output_path
```

- [ ] **Step 4: Run test to verify it passes**

```powershell
python -m unittest tests.test_raw_repository -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/comment_analysis/storage/raw.py src/comment_analysis/storage/__init__.py tests/test_raw_repository.py
git commit -m "feat: add RawFileRepository for API payload snapshots"
```

---

### Task 5: 采集层暴露 raw payload（支撑 P0-4）

**Files:**
- Modify: `src/comment_analysis/crawlers/sources/hackernews.py`
- Modify: `src/comment_analysis/crawlers/sources/stackexchange.py`
- Modify: `src/comment_analysis/entry/crawl.py`
- Test: `tests/test_collect_with_raw.py`（新建）

- [ ] **Step 1: Write the failing test**

```python
# tests/test_collect_with_raw.py
"""collect_with_raw 测试：mock 采集器返回 raw + records。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.entry.crawl import collect_with_raw
from comment_analysis.models import CommentRecord


class CollectWithRawTest(unittest.TestCase):
    def test_collect_with_raw_returns_platform_payloads(self) -> None:
        fake_record = CommentRecord(
            platform="hackernews",
            content="war update",
            source_url="https://example.com/1",
            crawl_time=datetime(2026, 6, 11, 10, 0, 0),
            comment_id="hn-1",
        )
        fake_crawler = MagicMock()
        fake_crawler.platform_name = "hackernews"
        fake_crawler.crawl_with_raw.return_value = (
            {"hits": [{"objectID": "hn-1"}]},
            [fake_record],
        )

        with patch("comment_analysis.entry.crawl._build_crawlers", return_value=[fake_crawler]):
            bundles = collect_with_raw(keyword="test", max_records=5, source="hackernews")

        self.assertEqual(len(bundles), 1)
        self.assertEqual(bundles[0]["platform"], "hackernews")
        self.assertIn("hits", bundles[0]["raw_payload"])
        self.assertEqual(bundles[0]["records"][0].comment_id, "hn-1")
        fake_crawler.close.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m unittest tests.test_collect_with_raw -v
```

Expected: FAIL — `collect_with_raw` 或 `crawl_with_raw` 不存在

- [ ] **Step 3: Write minimal implementation**

在各 Crawler 中新增方法（以 HN 为例）：

```python
def crawl_with_raw(self) -> tuple[dict[str, Any], list[CommentRecord]]:
    payload = self._fetch_payload()
    hits = payload.get("hits", [])
    if not isinstance(hits, list):
        raise RuntimeError("Hacker News 返回的评论列表格式不正确")
    valid_hits = [hit for hit in hits if isinstance(hit, dict)]
    crawl_time = datetime.now()
    records = self.parser.parse_many(self._build_parse_items(valid_hits, crawl_time))
    return payload, records
```

`crawl.py` 新增：

```python
def collect_with_raw(
    keyword: str = "美以伊战争",
    max_records: int = 20,
    source: str = "hackernews",
) -> list[dict[str, object]]:
    """采集并返回各平台的 raw payload 与 CommentRecord 列表。"""
    bundles: list[dict[str, object]] = []
    for crawler in _build_crawlers(keyword=keyword, max_records=max_records, source=source):
        try:
            raw_payload, records = crawler.crawl_with_raw()
            bundles.append(
                {
                    "platform": crawler.platform_name,
                    "raw_payload": raw_payload,
                    "records": records,
                }
            )
        finally:
            crawler.close()
    return bundles
```

`collect_records` 可改为内部调用 `collect_with_raw` 并 flatten records，保持向后兼容。

- [ ] **Step 4: Run test to verify it passes**

```powershell
python -m unittest tests.test_collect_with_raw tests.test_run_all -v
```

Expected: PASS（确保 `run_all` 仍绿）

- [ ] **Step 5: Commit**

```powershell
git add src/comment_analysis/crawlers/sources/hackernews.py src/comment_analysis/crawlers/sources/stackexchange.py src/comment_analysis/entry/crawl.py tests/test_collect_with_raw.py
git commit -m "feat: expose crawl_with_raw for offline raw replay"
```

---

### Task 6: 存储工厂（P0-5）

**Files:**
- Modify: `src/comment_analysis/storage/repository.py`
- Modify: `src/comment_analysis/storage/__init__.py`
- Modify: `src/comment_analysis/config/settings.py`（`storage_backend`）
- Test: `tests/test_build_repository.py`（新建）

- [ ] **Step 1: Write the failing test**

```python
# tests/test_build_repository.py
"""build_repository 工厂测试。"""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.storage import build_repository
from comment_analysis.storage.sqlite import SqliteCommentRepository
from comment_analysis.storage.repository import JsonFileRepository


class BuildRepositoryTest(unittest.TestCase):
    def test_default_backend_is_sqlite(self) -> None:
        with TemporaryDirectory() as temp_dir:
            db_url = f"sqlite:///{Path(temp_dir, 't.db').as_posix()}"
            repo = build_repository(backend="sqlite", database_url=db_url)
            self.assertIsInstance(repo, SqliteCommentRepository)
            if hasattr(repo, "close"):
                repo.close()

    def test_json_backend(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "out.json"
            repo = build_repository(backend="json", output_path=path)
            self.assertIsInstance(repo, JsonFileRepository)
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m unittest tests.test_build_repository -v
```

Expected: FAIL — `build_repository` 不存在

- [ ] **Step 3: Write minimal implementation**

```python
# repository.py 末尾新增
def build_repository(
    *,
    backend: str = "sqlite",
    database_url: str | None = None,
    output_path: Path | None = None,
    output_format: str = "json",
) -> BaseRepository | SqliteCommentRepository:
    normalized = backend.strip().lower()
    if normalized == "sqlite":
        from comment_analysis.storage.sqlite import SqliteCommentRepository
        from comment_analysis.config.settings import settings

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
```

`settings.py` 增加：

```python
storage_backend: str = os.getenv("STORAGE_BACKEND", "sqlite")
```

- [ ] **Step 4: Run test to verify it passes**

```powershell
python -m unittest tests.test_build_repository -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/comment_analysis/storage/repository.py src/comment_analysis/storage/__init__.py src/comment_analysis/config/settings.py tests/test_build_repository.py
git commit -m "feat: add build_repository factory with sqlite default"
```

---

### Task 7: FullPipeline 编排器（P0-6）

**Files:**
- Modify: `src/comment_analysis/pipeline/orchestrator.py`
- Test: `tests/test_full_pipeline.py`（新建）

- [ ] **Step 1: Write the failing test**

```python
# tests/test_full_pipeline.py
"""FullPipeline 集成测试（mock 采集）。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.models import CommentRecord
from comment_analysis.pipeline.orchestrator import FullPipeline


class FullPipelineTest(unittest.TestCase):
    def test_run_executes_all_stages(self) -> None:
        fake_record = CommentRecord(
            platform="hackernews",
            content="Iran Israel war",
            source_url="https://example.com/1",
            crawl_time=datetime(2026, 6, 11, 10, 0, 0),
            comment_id="hn-1",
        )
        fake_bundles = [
            {
                "platform": "hackernews",
                "raw_payload": {"hits": []},
                "records": [fake_record],
            }
        ]

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pipeline = FullPipeline(
                keyword="test",
                max_records=5,
                source="hackernews",
                database_url=f"sqlite:///{(temp_path / 'pipe.db').as_posix()}",
                raw_dir=temp_path / "raw",
                results_dir=temp_path / "results",
            )
            with patch(
                "comment_analysis.pipeline.orchestrator.collect_with_raw",
                return_value=fake_bundles,
            ):
                result = pipeline.run(top_n=5)

            self.assertTrue((temp_path / "raw" / "hackernews").exists())
            self.assertGreater(result["inserted_count"], 0)
            self.assertTrue(Path(result["report_json_path"]).exists())
            self.assertTrue(Path(result["report_html_path"]).exists())
            pipeline.close()
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m unittest tests.test_full_pipeline -v
```

Expected: FAIL — `FullPipeline` 不存在

- [ ] **Step 3: Write minimal implementation**

```python
# src/comment_analysis/pipeline/orchestrator.py
"""流程编排：串联采集、raw 落盘、清洗、SQLite、分析、HTML。"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from comment_analysis.analysis import assign_keywords, assign_sentiment, build_analysis_report
from comment_analysis.config.settings import settings
from comment_analysis.entry.clean import clean_records
from comment_analysis.entry.crawl import collect_with_raw
from comment_analysis.models import CrawlJob
from comment_analysis.storage.raw import RawFileRepository
from comment_analysis.storage.repository import build_repository
from comment_analysis.visualization import write_analysis_report


class PipelineOrchestrator:
    """保留旧接口，仅 crawl + save。"""
    # ... 现有代码不变 ...


class FullPipeline:
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
        self.keyword = keyword
        self.max_records = max_records
        self.source = source
        self.database_url = database_url or settings.database_url
        self.raw_dir = raw_dir or settings.raw_dir
        self.results_dir = results_dir or settings.results_dir
        self.storage_backend = storage_backend
        self._repo = build_repository(
            backend=storage_backend,
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
            raw_count += len(bundle["records"])
            all_records.extend(bundle["records"])

        cleaned = clean_records(all_records)
        inserted = self._repo.save_many(cleaned, job_id=job_id)

        enriched = assign_sentiment(assign_keywords(cleaned, top_n=per_record_top_n))
        report = build_analysis_report(enriched, top_n=top_n)

        self.results_dir.mkdir(parents=True, exist_ok=True)
        report_json_path = self.results_dir / f"job_{job_id}_analysis.json"
        report_json_path.write_text(
            __import__("json").dumps(report, ensure_ascii=False, indent=2),
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

    def close(self) -> None:
        if hasattr(self._repo, "close"):
            self._repo.close()
```

- [ ] **Step 4: Run test to verify it passes**

```powershell
python -m unittest tests.test_full_pipeline -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/comment_analysis/pipeline/orchestrator.py tests/test_full_pipeline.py
git commit -m "feat: add FullPipeline orchestrating crawl to HTML report"
```

---

### Task 8: 统一入口 `entry/pipeline.py`（P0-1）

**Files:**
- Create: `src/comment_analysis/entry/pipeline.py`
- Test: `tests/test_pipeline_entry.py`（新建）

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pipeline_entry.py
"""pipeline CLI 入口测试。"""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.entry.pipeline import run_full_pipeline


class PipelineEntryTest(unittest.TestCase):
    def test_run_full_pipeline_delegates_to_full_pipeline(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with patch("comment_analysis.entry.pipeline.FullPipeline") as mock_cls:
                instance = mock_cls.return_value
                instance.run.return_value = {
                    "job_id": "job-x",
                    "database_url": "sqlite:///x.db",
                    "report_json_path": Path(temp_dir) / "a.json",
                    "report_html_path": Path(temp_dir) / "a.html",
                    "inserted_count": 3,
                    "raw_count": 3,
                    "cleaned_count": 3,
                }
                result = run_full_pipeline(
                    keyword="test",
                    limit=5,
                    source="hackernews",
                    results_dir=Path(temp_dir),
                )
                self.assertEqual(result["job_id"], "job-x")
                instance.run.assert_called_once()
                instance.close.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m unittest tests.test_pipeline_entry -v
```

Expected: FAIL — module `pipeline` not found

- [ ] **Step 3: Write minimal implementation**

```python
# src/comment_analysis/entry/pipeline.py
"""全链路入口：采集 → raw → 清洗 → SQLite → 分析 → HTML。"""

from __future__ import annotations

import argparse
from pathlib import Path

from comment_analysis.config.settings import settings
from comment_analysis.pipeline.orchestrator import FullPipeline


def run_full_pipeline(
    keyword: str = "美以伊战争",
    limit: int = 20,
    source: str = "all",
    top_n: int = 20,
    per_record_top_n: int = 5,
    results_dir: Path | None = None,
    storage_backend: str | None = None,
) -> dict[str, object]:
    pipeline = FullPipeline(
        keyword=keyword,
        max_records=limit,
        source=source,
        storage_backend=storage_backend or settings.storage_backend,
        results_dir=results_dir,
    )
    try:
        return pipeline.run(top_n=top_n, per_record_top_n=per_record_top_n)
    finally:
        pipeline.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="运行评论分析全链路")
    parser.add_argument("--keyword", default="美以伊战争")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--source", default="all", choices=("hackernews", "stackexchange", "all"))
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--per-record-top-n", type=int, default=5)
    parser.add_argument("--output-dir", default="", help="结果目录，默认 data/results")
    parser.add_argument(
        "--storage-backend",
        default="",
        choices=("sqlite", "json", "csv"),
        help="存储后端，默认 sqlite",
    )
    args = parser.parse_args()

    results_dir = Path(args.output_dir).resolve() if args.output_dir else None
    result = run_full_pipeline(
        keyword=args.keyword,
        limit=args.limit,
        source=args.source,
        top_n=args.top_n,
        per_record_top_n=args.per_record_top_n,
        results_dir=results_dir,
        storage_backend=args.storage_backend or None,
    )

    print("全链路执行完成")
    print(f"任务 ID：{result['job_id']}")
    print(f"数据库：{result['database_url']}")
    print(f"采集/清洗：{result['raw_count']} / {result['cleaned_count']}")
    print(f"新入库：{result['inserted_count']}")
    print(f"JSON 报告：{result['report_json_path']}")
    print(f"HTML 仪表盘：{result['report_html_path']}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

```powershell
python -m unittest tests.test_pipeline_entry -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/comment_analysis/entry/pipeline.py tests/test_pipeline_entry.py
git commit -m "feat: add pipeline CLI entry for one-command full run"
```

---

### Task 9: 分析接库（P0-8）

**Files:**
- Modify: `src/comment_analysis/entry/analyze.py`
- Test: `tests/test_analyze_from_db.py`（新建）

- [ ] **Step 1: Write the failing test**

```python
# tests/test_analyze_from_db.py
"""analyze --from-db 测试。"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.entry.analyze import run_analysis_from_db
from comment_analysis.models import CommentRecord, CrawlJob
from comment_analysis.storage.sqlite import SqliteCommentRepository


class AnalyzeFromDbTest(unittest.TestCase):
    def test_run_analysis_from_db_by_job_id(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_url = f"sqlite:///{(temp_path / 'a.db').as_posix()}"
            repo = SqliteCommentRepository(db_url)
            job_id = "job-analyze-1"
            repo.create_crawl_job(
                CrawlJob(
                    job_id=job_id,
                    keyword="test",
                    source="hackernews",
                    status="completed",
                    started_at=datetime(2026, 6, 11, 10, 0, 0),
                )
            )
            repo.save_many(
                [
                    CommentRecord(
                        platform="hackernews",
                        content="Iran Israel war update",
                        source_url="https://example.com/1",
                        crawl_time=datetime(2026, 6, 11, 10, 0, 0),
                        comment_id="c1",
                    )
                ],
                job_id=job_id,
            )

            result = run_analysis_from_db(
                database_url=db_url,
                job_id=job_id,
                output_dir=temp_path / "results",
                top_n=5,
            )
            report = json.loads(Path(result["output_path"]).read_text(encoding="utf-8"))
            self.assertEqual(report["total_records"], 1)
            self.assertTrue(Path(result["report_path"]).exists())
            repo.close()
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m unittest tests.test_analyze_from_db -v
```

Expected: FAIL — `run_analysis_from_db` 不存在

- [ ] **Step 3: Write minimal implementation**

在 `analyze.py` 新增：

```python
from comment_analysis.storage.sqlite import SqliteCommentRepository


def run_analysis_from_db(
    *,
    database_url: str,
    job_id: str | None = None,
    last_job: bool = False,
    output_dir: Path | None = None,
    top_n: int = 20,
    per_record_top_n: int = 5,
) -> dict[str, object]:
    repo = SqliteCommentRepository(database_url)
    try:
        resolved_job_id = job_id
        if last_job and not resolved_job_id:
            resolved_job_id = repo.get_last_crawl_job_id()
        if not resolved_job_id:
            raise ValueError("需要 --job-id 或 --last-job")

        records = repo.fetch_comments(job_id=resolved_job_id)
        if not records:
            raise ValueError(f"job {resolved_job_id} 下没有评论数据")

        records_with_keywords = assign_keywords(records, top_n=per_record_top_n)
        enriched_records = assign_sentiment(records_with_keywords)
        report = build_analysis_report(enriched_records, top_n=top_n)

        target_dir = output_dir or settings.results_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = target_dir / f"job_{resolved_job_id}_analysis_{timestamp}.json"
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        report_path = write_analysis_report(report, target_dir, output_path.stem)

        return {
            "job_id": resolved_job_id,
            "database_url": database_url,
            "output_path": output_path,
            "report_path": report_path,
            "total_records": report["total_records"],
        }
    finally:
        repo.close()
```

`main()` 改为互斥参数组：

```python
parser.add_argument("input_path", nargs="?", default="", help="JSON/CSV 文件路径")
parser.add_argument("--from-db", action="store_true", help="从 SQLite 读取")
parser.add_argument("--job-id", default="", help="指定 crawl job_id")
parser.add_argument("--last-job", action="store_true", help="使用最近一次 crawl job")
parser.add_argument("--database-url", default="", help="覆盖 DATABASE_URL")
```

分支逻辑：`--from-db` 时调用 `run_analysis_from_db`，否则保持现有文件路径逻辑。

- [ ] **Step 4: Run test to verify it passes**

```powershell
python -m unittest tests.test_analyze_from_db tests.test_analyze_entry -v
```

Expected: PASS（新旧分析入口均绿）

- [ ] **Step 5: Commit**

```powershell
git add src/comment_analysis/entry/analyze.py tests/test_analyze_from_db.py
git commit -m "feat: analyze comments from SQLite by job_id or last job"
```

---

### Task 10: 全量回归与手工验收

**Files:**
- Modify: `tests/test_run_all.py`（如 `save_many` 返回值变更导致断言失败则修复）

- [ ] **Step 1: Run full test suite**

```powershell
cd D:\comment-analysis
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

Expected: 全部 PASS

- [ ] **Step 2: Manual smoke test（需联网）**

```powershell
pip install -r requirements.txt
copy .env.example .env
python -m comment_analysis.entry.pipeline --keyword "美以伊战争" --limit 5 --source all
```

Expected 终端输出包含：
- `任务 ID：2026...`
- `数据库：sqlite:///...comment_analysis.db`
- `JSON 报告：...data\results\...`
- `HTML 仪表盘：...data\results\...`

- [ ] **Step 3: Verify DB + raw + re-analyze**

```powershell
python -m comment_analysis.entry.analyze --from-db --last-job --output-dir data\results
```

Expected: 不依赖 `data\processed\comments_*.json`，仍能生成新报告。

检查文件：
- `data\comment_analysis.db` 存在
- `data\raw\hackernews\{job_id}.json` 与 `data\raw\stackexchange\{job_id}.json` 存在（`--source all` 时）

- [ ] **Step 4: Commit any test fixes**

```powershell
git add tests/
git commit -m "test: fix regressions after P0 pipeline integration"
```

---

## P0 验收清单（对应 PROJECT_BACKLOG 第六节）

| ID | 验收项 | 对应 Task |
|----|--------|-----------|
| P0-1 | `python -m comment_analysis.entry.pipeline` 一条命令跑通 | Task 8 + 10 |
| P0-2 | SQLite 去重入库，可按平台/时间查询 | Task 3 |
| P0-3 | `crawl_jobs` 表记录任务元数据 | Task 2 + 3 + 7 |
| P0-4 | `data/raw/{platform}/{job_id}.json` | Task 4 + 5 + 7 |
| P0-5 | `build_repository` 默认 sqlite | Task 6 |
| P0-6 | `FullPipeline` 串联各阶段 | Task 7 |
| P0-7 | `requirements.txt` + dotenv | Task 1 |
| P0-8 | `analyze --from-db --last-job` | Task 9 |

---

## 自审（Spec Coverage）

| Backlog 要求 | 计划覆盖 |
|--------------|----------|
| 一键全链路 | Task 7、8、10 |
| SQLite 主存储 + 去重 | Task 3 |
| crawl_jobs 可追溯 | Task 2、3、7 |
| raw 落盘 + 离线重跑基础 | Task 4、5（重跑 CLI 可留 P2） |
| 存储工厂默认 sqlite | Task 6 |
| 编排器串联 | Task 7 |
| requirements + dotenv | Task 1 |
| analyze 读库 | Task 9 |
| 双语分析（P1） | **不在本计划** — 刻意排除 |
| analysis_jobs 表 | **不在 P0** — 归入 P2 任务元数据加固 |

---

## 风险与约束

1. **`comment_id` 为空** 的记录会被 SQLite 层跳过 dedup 插入；与现有清洗逻辑一致，Accept。
2. **Windows 路径**：`DATABASE_URL` 使用 `as_posix()` 避免反斜杠转义问题。
3. **`run_all` 保留**：不删除现有入口；`pipeline` 为新主路径。
4. **Stack Exchange `crawl_with_raw`**：实现方式与 HN 对称，返回完整 API JSON。
5. **P1 前置**：本计划完成后，P1 可在 `assign_keywords` / `assign_sentiment` 内替换分词实现，无需改动 pipeline 骨架。

---

## 预估工时

| Task | 预估 |
|------|------|
| Task 1–2 | 0.5 天 |
| Task 3–4 | 1 天 |
| Task 5–6 | 0.5 天 |
| Task 7–9 | 1 天 |
| Task 10 | 0.5 天 |
| **合计** | **约 3.5 个工作日**（与 Backlog 阶段 1「1～2 周」一致，留缓冲给 code review） |
